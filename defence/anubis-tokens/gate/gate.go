// Package gate is a Privacy Pass front door for Anubis (C5).
//
// Anubis (TecharoHQ/anubis) makes every visitor pay proof of work and gives back a cookie. Its issues #119 and #326
// ask for Privacy Pass so that a visitor who already paid, or who holds a token from a trusted issuer, can skip the
// work without a cookie that links its visits. Anubis has no token or Web Bot Auth code (v1.28.2, checked
// 2026-11-03), so this gate sits in front of an unmodified Anubis and adds three paths:
//
//   - Issuer (RFC 9578, token type 2, publicly verifiable blind RSA): a visitor holding a valid Anubis pass cookie
//     may fetch up to N blind-signed tokens. The gate never sees the token it signs, so a token spent later cannot
//     be linked to the pass that paid for it.
//   - Redemption (RFC 9577 "PrivateToken" HTTP auth): a request carrying a valid, unspent token from a trusted
//     issuer goes straight to the backend, skipping Anubis. Requests without one get Anubis, plus a
//     WWW-Authenticate challenge so token-aware clients know where to get tokens.
//   - Web Bot Auth: a request with a valid agent signature goes straight to the backend too. Verification is
//     delegated to the observatory's verifier (Cloudflare's reference library), so the stack has one WBA
//     implementation.
//
// Crypto is Cloudflare's pat-go (BSD-3); JWT checks use golang-jwt (the library Anubis itself uses).
package gate

import (
	"bytes"
	"context"
	"crypto"
	"crypto/ed25519"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/sha512"
	"crypto/subtle"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/cloudflare/pat-go/tokens"
	"github.com/cloudflare/pat-go/tokens/type2"
	"github.com/cloudflare/pat-go/util"
	"github.com/golang-jwt/jwt/v5"
)

const (
	DirectoryPath        = "/.well-known/private-token-issuer-directory"
	RequestPath          = "/.well-known/private-token-request"
	DirectoryContentType = "application/private-token-issuer-directory"
	RequestContentType   = "application/private-token-request"
	ResponseContentType  = "application/private-token-response"
	TokenType            = type2.BasicPublicTokenType
	GateHeader           = "X-Gate-Pass"
)

// Issuer is one issuer whose tokens the gate accepts: its name (as written in the challenge) and token key.
type Issuer struct {
	Name     string
	Key      *rsa.PublicKey
	KeyID    []byte // sha256 of the SPKI (RSASSA-PSS OID) encoding, RFC 9578 §6.5
	KeyB64   string // base64url of that encoding, for the challenge's token-key parameter
	External bool
}

// NewIssuer builds an Issuer from a public key.
func NewIssuer(name string, key *rsa.PublicKey, external bool) (Issuer, error) {
	enc, err := util.MarshalTokenKeyPSSOID(key)
	if err != nil {
		return Issuer{}, err
	}
	id := sha256.Sum256(enc)
	return Issuer{Name: name, Key: key, KeyID: id[:], KeyB64: base64.RawURLEncoding.EncodeToString(enc), External: external}, nil
}

// Challenge is the TokenChallenge this origin issues for an issuer: no redemption context (tokens can be fetched
// ahead of time), origin_info bound to this site, so a token is only good here.
func (i Issuer) Challenge(origin string) tokens.TokenChallenge {
	return tokens.TokenChallenge{TokenType: TokenType, IssuerName: i.Name, RedemptionNonce: nil, OriginInfo: []string{origin}}
}

type Config struct {
	Origin        string            // origin_info written into challenges, e.g. "anubis.captcharena.org"
	IssuerKey     *rsa.PrivateKey   // our own issuer key (Anubis-as-issuer)
	IssuerName    string            // name of our own issuer
	External      []Issuer          // other issuers we trust (e.g. the C7 process-check issuer)
	AnubisPub     ed25519.PublicKey // verifies Anubis pass cookies (JWT, EdDSA)
	TokensPerPass int               // how many tokens one PoW pass may buy
	Anubis        *url.URL          // upstream for everyone without a token
	Backend       *url.URL          // upstream for token holders and verified agents
	WBAVerifyURL  string            // observatory /api/verify-request; empty disables the WBA path
	AllowTestKeys bool              // accept WBA signatures made with published RFC 9421 test keys
	SpentLog      string            // append-only file of spent token nonces (survives restarts); empty = memory only
	RealIPHeader  string            // header carrying the client IP set by the edge (CF-Connecting-IP); empty = socket
	Logger        *slog.Logger
	HTTPClient    *http.Client
	Now           func() time.Time
}

type Gate struct {
	cfg      Config
	own      Issuer
	issuers  []Issuer
	toAnubis *httputil.ReverseProxy
	toBack   *httputil.ReverseProxy

	mu     sync.Mutex
	spent  map[[32]byte]struct{}
	issued map[string]int // Anubis challenge ID -> tokens issued for that pass
	spentF *os.File

	Stats Stats
}

// Stats are counters for the demo page and tests.
type Stats struct {
	mu                                                          sync.Mutex
	Issued, Redeemed, DoubleSpend, BadToken, WBAPass, WBAReject int
	ToAnubis, IssueRefused                                      int
}

func (s *Stats) inc(f *int) { s.mu.Lock(); *f++; s.mu.Unlock() }

// Snapshot returns a copy of the counters.
func (s *Stats) Snapshot() map[string]int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return map[string]int{"issued": s.Issued, "redeemed": s.Redeemed, "double_spend": s.DoubleSpend, "bad_token": s.BadToken,
		"wba_pass": s.WBAPass, "wba_reject": s.WBAReject, "to_anubis": s.ToAnubis, "issue_refused": s.IssueRefused}
}

func New(cfg Config) (*Gate, error) {
	if cfg.Logger == nil {
		cfg.Logger = slog.Default()
	}
	if cfg.HTTPClient == nil {
		cfg.HTTPClient = &http.Client{Timeout: 5 * time.Second}
	}
	if cfg.Now == nil {
		cfg.Now = time.Now
	}
	if cfg.TokensPerPass <= 0 {
		cfg.TokensPerPass = 10
	}
	own, err := NewIssuer(cfg.IssuerName, &cfg.IssuerKey.PublicKey, false)
	if err != nil {
		return nil, err
	}
	g := &Gate{cfg: cfg, own: own, issuers: append([]Issuer{own}, cfg.External...), spent: map[[32]byte]struct{}{}, issued: map[string]int{}}
	g.toAnubis = proxy(cfg.Anubis)
	g.toBack = proxy(cfg.Backend)
	if cfg.SpentLog != "" {
		if err := g.loadSpent(); err != nil {
			return nil, err
		}
	}
	return g, nil
}

func proxy(target *url.URL) *httputil.ReverseProxy {
	return &httputil.ReverseProxy{Rewrite: func(r *httputil.ProxyRequest) {
		r.SetURL(target)
		r.Out.Host = r.In.Host // keep the public Host: Anubis and the backend see the site name
		r.Out.Header["X-Forwarded-For"] = r.In.Header["X-Forwarded-For"]
		r.SetXForwarded()
		if p := r.In.Header.Get("X-Forwarded-Proto"); p == "https" {
			r.Out.Header.Set("X-Forwarded-Proto", p) // the edge (cloudflared) terminated TLS
		}
	}}
}

func (g *Gate) loadSpent() error {
	data, err := os.ReadFile(g.cfg.SpentLog)
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		return err
	}
	for _, line := range strings.Split(string(data), "\n") {
		if b, err := hex.DecodeString(strings.TrimSpace(line)); err == nil && len(b) == 32 {
			g.spent[[32]byte(b)] = struct{}{}
		}
	}
	f, err := os.OpenFile(g.cfg.SpentLog, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o600)
	if err != nil {
		return err
	}
	g.spentF = f
	return nil
}

// --- HTTP ---------------------------------------------------------------------------------------------------------

func (g *Gate) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	r.Header.Del(GateHeader) // only the gate sets this
	ip := g.clientIP(r)
	r.Header.Set("X-Real-IP", ip) // Anubis needs it (and binds its JWT to it)

	switch r.URL.Path {
	case DirectoryPath:
		g.serveDirectory(w, r)
		return
	case RequestPath:
		g.serveIssue(w, r, ip)
		return
	case "/.well-known/ppgate-stats":
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(g.Stats.Snapshot())
		return
	}

	if auth := r.Header.Get("Authorization"); strings.HasPrefix(strings.ToLower(auth), "privatetoken ") {
		raw, err := parseTokenAuth(auth)
		if err == nil {
			err = g.Redeem(raw)
		}
		if err != nil {
			if errors.Is(err, ErrDoubleSpend) {
				g.Stats.inc(&g.Stats.DoubleSpend)
			} else {
				g.Stats.inc(&g.Stats.BadToken)
			}
			g.cfg.Logger.Info("token refused", "err", err)
			g.challengeHeaders(w)
			http.Error(w, "token refused: "+err.Error()+"\n", http.StatusUnauthorized)
			return
		}
		g.Stats.inc(&g.Stats.Redeemed)
		r.Header.Del("Authorization")
		r.Header.Set(GateHeader, "privacy-pass")
		g.toBack.ServeHTTP(w, r)
		return
	}

	if g.cfg.WBAVerifyURL != "" && r.Header.Get("Signature") != "" {
		agent, err := g.verifyWBA(r.Context(), r)
		if err == nil {
			g.Stats.inc(&g.Stats.WBAPass)
			r.Header.Set(GateHeader, "web-bot-auth; agent="+agent)
			g.toBack.ServeHTTP(w, r)
			return
		}
		g.Stats.inc(&g.Stats.WBAReject)
		g.cfg.Logger.Info("signature not accepted, sending to Anubis", "err", err)
	}

	g.Stats.inc(&g.Stats.ToAnubis)
	g.challengeHeaders(w)
	g.toAnubis.ServeHTTP(w, r)
}

func (g *Gate) clientIP(r *http.Request) string {
	if g.cfg.RealIPHeader != "" {
		if v := strings.TrimSpace(r.Header.Get(g.cfg.RealIPHeader)); net.ParseIP(v) != nil {
			return v
		}
	}
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		return r.RemoteAddr
	}
	return host
}

// challengeHeaders adds one RFC 9577 challenge per trusted issuer.
func (g *Gate) challengeHeaders(w http.ResponseWriter) {
	var parts []string
	for _, is := range g.issuers {
		c := base64.RawURLEncoding.EncodeToString(is.Challenge(g.cfg.Origin).Marshal())
		parts = append(parts, fmt.Sprintf(`PrivateToken challenge="%s", token-key="%s"`, c, is.KeyB64))
	}
	w.Header().Set("WWW-Authenticate", strings.Join(parts, ", "))
}

func (g *Gate) serveDirectory(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", DirectoryContentType)
	w.Header().Set("Cache-Control", "max-age=3600")
	_ = json.NewEncoder(w).Encode(map[string]any{
		"issuer-request-uri": RequestPath,
		"token-keys":         []map[string]any{{"token-type": TokenType, "token-key": g.own.KeyB64}},
	})
}

func (g *Gate) serveIssue(w http.ResponseWriter, r *http.Request, ip string) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST only", http.StatusMethodNotAllowed)
		return
	}
	if ct := strings.TrimSpace(strings.Split(r.Header.Get("Content-Type"), ";")[0]); ct != RequestContentType {
		http.Error(w, "content-type must be "+RequestContentType, http.StatusUnsupportedMediaType)
		return
	}
	pass, err := g.AnubisPass(r, ip)
	if err != nil {
		g.Stats.inc(&g.Stats.IssueRefused)
		http.Error(w, "no valid Anubis pass: solve the proof of work first ("+err.Error()+")\n", http.StatusForbidden)
		return
	}
	body, err := io.ReadAll(io.LimitReader(r.Body, 1024))
	if err != nil {
		http.Error(w, "bad body", http.StatusBadRequest)
		return
	}
	sig, err := g.Issue(pass, body)
	if err != nil {
		g.Stats.inc(&g.Stats.IssueRefused)
		status := http.StatusBadRequest
		if errors.Is(err, ErrPassExhausted) {
			status = http.StatusTooManyRequests
		}
		http.Error(w, err.Error()+"\n", status)
		return
	}
	g.Stats.inc(&g.Stats.Issued)
	w.Header().Set("Content-Type", ResponseContentType)
	w.Header().Set("Cache-Control", "no-store")
	_, _ = w.Write(sig)
}

// --- issuance -----------------------------------------------------------------------------------------------------

var (
	ErrPassExhausted = errors.New("this proof-of-work pass has already bought its tokens")
	ErrDoubleSpend   = errors.New("token already spent")
)

// AnubisPass checks the Anubis pass cookie (an EdDSA JWT; any cookie name, since Anubis may add a suffix) and
// returns the challenge ID it was issued for. Mirrors Anubis's own checks: signature, expiry, and the IP binding
// (JWT_RESTRICTION_HEADER=X-Real-IP, Anubis's default).
func (g *Gate) AnubisPass(r *http.Request, ip string) (string, error) {
	var lastErr error = errors.New("no Anubis cookie")
	for _, c := range r.Cookies() {
		if strings.Count(c.Value, ".") != 2 {
			continue
		}
		tok, err := jwt.Parse(c.Value, func(t *jwt.Token) (any, error) { return g.cfg.AnubisPub, nil },
			jwt.WithValidMethods([]string{"EdDSA"}), jwt.WithExpirationRequired(), jwt.WithTimeFunc(g.cfg.Now))
		if err != nil {
			lastErr = err
			continue
		}
		claims, _ := tok.Claims.(jwt.MapClaims)
		id, _ := claims["challenge"].(string)
		if id == "" {
			lastErr = errors.New("pass has no challenge id")
			continue
		}
		if res, ok := claims["restriction"].(string); ok {
			sum := sha256.Sum256([]byte(ip))
			if subtle.ConstantTimeCompare([]byte(res), []byte(hex.EncodeToString(sum[:]))) != 1 {
				lastErr = errors.New("pass was issued to another IP")
				continue
			}
		}
		return id, nil
	}
	return "", lastErr
}

// Issue blind-signs one TokenRequest for the holder of pass, up to TokensPerPass per pass.
func (g *Gate) Issue(pass string, body []byte) ([]byte, error) {
	var req type2.BasicPublicTokenRequest
	if !req.Unmarshal(body) || len(body) != 3+256 {
		return nil, errors.New("not a type-2 TokenRequest")
	}
	if req.TokenKeyID != g.own.KeyID[31] {
		return nil, errors.New("TokenRequest is for another key")
	}
	g.mu.Lock()
	if g.issued[pass] >= g.cfg.TokensPerPass {
		g.mu.Unlock()
		return nil, ErrPassExhausted
	}
	g.issued[pass]++
	g.mu.Unlock()
	return type2.NewBasicPublicIssuer(g.cfg.IssuerKey).Evaluate(&req)
}

// --- redemption ---------------------------------------------------------------------------------------------------

func parseTokenAuth(h string) ([]byte, error) {
	rest := strings.TrimSpace(h[len("PrivateToken "):])
	for _, p := range strings.Split(rest, ",") {
		k, v, ok := strings.Cut(strings.TrimSpace(p), "=")
		if !ok || !strings.EqualFold(strings.TrimSpace(k), "token") {
			continue
		}
		v = strings.Trim(strings.TrimSpace(v), `"`)
		if b, err := base64.RawURLEncoding.DecodeString(strings.TrimRight(v, "=")); err == nil {
			return b, nil
		}
		return nil, errors.New("token is not base64url")
	}
	return nil, errors.New("no token parameter")
}

// Redeem verifies a type-2 token against the trusted issuers and this origin's challenge, then marks it spent.
func (g *Gate) Redeem(raw []byte) error {
	tok, err := type2.UnmarshalToken(raw)
	if err != nil || tok.TokenType != TokenType {
		return errors.New("not a type-2 token")
	}
	var issuer *Issuer
	for i := range g.issuers {
		if bytes.Equal(g.issuers[i].KeyID, tok.KeyID) {
			issuer = &g.issuers[i]
			break
		}
	}
	if issuer == nil {
		return errors.New("token is from an issuer this site does not trust")
	}
	want := sha256.Sum256(issuer.Challenge(g.cfg.Origin).Marshal())
	if !bytes.Equal(tok.Context, want[:]) {
		return errors.New("token was made for another site or challenge")
	}
	digest := sha512.Sum384(tok.AuthenticatorInput())
	if err := rsa.VerifyPSS(issuer.Key, crypto.SHA384, digest[:], tok.Authenticator, &rsa.PSSOptions{SaltLength: 48, Hash: crypto.SHA384}); err != nil {
		return errors.New("token signature does not verify")
	}
	// Spent set keyed by the token nonce. Kept in memory and appended to SpentLog so a restart cannot reopen it.
	key := sha256.Sum256(append(append([]byte{}, tok.KeyID...), tok.Nonce...))
	g.mu.Lock()
	defer g.mu.Unlock()
	if _, dup := g.spent[key]; dup {
		return ErrDoubleSpend
	}
	g.spent[key] = struct{}{}
	if g.spentF != nil {
		if _, err := fmt.Fprintln(g.spentF, hex.EncodeToString(key[:])); err != nil {
			return fmt.Errorf("could not record spend: %w", err)
		}
	}
	return nil
}

// --- Web Bot Auth (delegated) ---------------------------------------------------------------------------------------

func (g *Gate) verifyWBA(ctx context.Context, r *http.Request) (string, error) {
	headers := map[string][]string{}
	for k, v := range r.Header {
		lk := strings.ToLower(k)
		if lk == "signature" || lk == "signature-input" || lk == "signature-agent" || lk == "user-agent" {
			headers[lk] = v
		}
	}
	headers["host"] = []string{r.Host}
	scheme := "http"
	if r.Header.Get("X-Forwarded-Proto") == "https" {
		scheme = "https"
	}
	body, _ := json.Marshal(map[string]any{"method": r.Method, "url": scheme + "://" + r.Host + r.URL.RequestURI(), "headers": headers})
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, g.cfg.WBAVerifyURL, bytes.NewReader(body))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")
	res, err := g.cfg.HTTPClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("verifier unreachable: %w", err)
	}
	defer res.Body.Close()
	var v struct {
		Outcome        string `json:"outcome"`
		Category       string `json:"category"`
		TestKey        bool   `json:"testKey"`
		SignatureAgent struct {
			URI string `json:"uri"`
		} `json:"signatureAgent"`
	}
	if err := json.NewDecoder(io.LimitReader(res.Body, 1<<16)).Decode(&v); err != nil {
		return "", fmt.Errorf("verifier reply: %w", err)
	}
	if v.Outcome != "valid" {
		return "", fmt.Errorf("signature %s (%s)", v.Outcome, v.Category)
	}
	if v.TestKey && !g.cfg.AllowTestKeys {
		return "", errors.New("signature made with a published test key")
	}
	agent := "thumbprint-only"
	if u, err := url.Parse(v.SignatureAgent.URI); err == nil && u.Host != "" {
		agent = u.Host
	}
	return agent, nil
}
