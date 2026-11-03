package gate

import (
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/cloudflare/pat-go/tokens/type2"
	"github.com/golang-jwt/jwt/v5"
)

var (
	issuerKey, _             = rsa.GenerateKey(rand.Reader, 2048)
	otherKey, _              = rsa.GenerateKey(rand.Reader, 2048)
	anubisPub, anubisPriv, _ = ed25519.GenerateKey(rand.Reader)
)

const origin = "site.test"

type world struct {
	g                       *Gate
	backend, anubis         *httptest.Server
	backendHits, anubisHits int
	srv                     *httptest.Server
}

func newWorld(t *testing.T, mod func(*Config)) *world {
	t.Helper()
	w := &world{}
	w.backend = httptest.NewServer(http.HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		w.backendHits++
		fmt.Fprintf(rw, "backend; gate=%s", r.Header.Get(GateHeader))
	}))
	w.anubis = httptest.NewServer(http.HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		w.anubisHits++
		fmt.Fprint(rw, "anubis challenge page")
	}))
	bu, _ := url.Parse(w.backend.URL)
	au, _ := url.Parse(w.anubis.URL)
	cfg := Config{Origin: origin, IssuerName: "issuer.test", IssuerKey: issuerKey, AnubisPub: anubisPub, TokensPerPass: 3, Anubis: au, Backend: bu,
		SpentLog: filepath.Join(t.TempDir(), "spent.log")}
	if mod != nil {
		mod(&cfg)
	}
	g, err := New(cfg)
	if err != nil {
		t.Fatal(err)
	}
	w.g = g
	w.srv = httptest.NewServer(g)
	t.Cleanup(func() { w.srv.Close(); w.backend.Close(); w.anubis.Close() })
	return w
}

func anubisCookie(t *testing.T, challenge, ip string, exp time.Time, key ed25519.PrivateKey) string {
	t.Helper()
	sum := sha256.Sum256([]byte(ip))
	claims := jwt.MapClaims{"challenge": challenge, "method": "fast", "policyRule": "x", "action": "CHALLENGE", "exp": exp.Unix(), "iat": time.Now().Unix(), "restriction": hex.EncodeToString(sum[:])}
	s, err := jwt.NewWithClaims(jwt.SigningMethodEdDSA, claims).SignedString(key)
	if err != nil {
		t.Fatal(err)
	}
	return "techaro.lol-anubis-auth-1a2b3c4d=" + s
}

// mintToken runs the client half (pat-go) against the gate's issuer endpoint over HTTP.
func mintToken(t *testing.T, w *world, cookie string, is Issuer, originInfo string) ([]byte, int, string) {
	t.Helper()
	challenge := is.Challenge(originInfo).Marshal()
	nonce := make([]byte, 32)
	_, _ = rand.Read(nonce)
	state, err := type2.NewBasicPublicClient().CreateTokenRequest(challenge, nonce, is.KeyID, is.Key)
	if err != nil {
		t.Fatal(err)
	}
	req, _ := http.NewRequest(http.MethodPost, w.srv.URL+RequestPath, bytes.NewReader(state.Request().Marshal()))
	req.Header.Set("Content-Type", RequestContentType)
	if cookie != "" {
		req.Header.Set("Cookie", cookie)
	}
	res, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	body, _ := io.ReadAll(res.Body)
	res.Body.Close()
	if res.StatusCode != 200 {
		return nil, res.StatusCode, string(body)
	}
	tok, err := state.FinalizeToken(body)
	if err != nil {
		t.Fatal(err)
	}
	return tok.Marshal(), 200, ""
}

func get(t *testing.T, w *world, headers map[string]string) (int, string) {
	t.Helper()
	req, _ := http.NewRequest(http.MethodGet, w.srv.URL+"/page", nil)
	for k, v := range headers {
		req.Header.Set(k, v)
	}
	res, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	body, _ := io.ReadAll(res.Body)
	res.Body.Close()
	return res.StatusCode, string(body)
}

func auth(tok []byte) map[string]string {
	return map[string]string{"Authorization": `PrivateToken token="` + base64.RawURLEncoding.EncodeToString(tok) + `"`}
}

func TestTokenSkipsAnubisAndCannotBeSpentTwice(t *testing.T) {
	w := newWorld(t, nil)
	tok, code, msg := mintToken(t, w, anubisCookie(t, "pass-1", "127.0.0.1", time.Now().Add(time.Hour), anubisPriv), w.g.own, origin)
	if code != 200 {
		t.Fatalf("issue: %d %s", code, msg)
	}
	if code, body := get(t, w, auth(tok)); code != 200 || body != "backend; gate=privacy-pass" {
		t.Fatalf("redeem: %d %q", code, body)
	}
	if w.anubisHits != 0 {
		t.Fatal("token holder was sent to Anubis")
	}
	if code, body := get(t, w, auth(tok)); code != 401 || !strings.Contains(body, "already spent") {
		t.Fatalf("double spend: %d %q", code, body)
	}
}

func TestNoTokenGoesToAnubisWithChallengeHeader(t *testing.T) {
	w := newWorld(t, nil)
	res, err := http.Get(w.srv.URL + "/page")
	if err != nil {
		t.Fatal(err)
	}
	body, _ := io.ReadAll(res.Body)
	res.Body.Close()
	if string(body) != "anubis challenge page" || w.backendHits != 0 {
		t.Fatalf("got %q", body)
	}
	h := res.Header.Get("WWW-Authenticate")
	if !strings.HasPrefix(h, `PrivateToken challenge="`) || !strings.Contains(h, w.g.own.KeyB64) {
		t.Fatalf("challenge header: %q", h)
	}
}

func TestIssuanceNeedsAValidPass(t *testing.T) {
	w := newWorld(t, nil)
	_, otherPriv, _ := ed25519.GenerateKey(rand.Reader)
	cases := map[string]string{
		"no cookie":                  "",
		"expired pass":               anubisCookie(t, "p", "127.0.0.1", time.Now().Add(-time.Minute), anubisPriv),
		"pass from a stranger's key": anubisCookie(t, "p", "127.0.0.1", time.Now().Add(time.Hour), otherPriv),
		"pass bound to another IP":   anubisCookie(t, "p", "10.9.9.9", time.Now().Add(time.Hour), anubisPriv),
		"garbage":                    "techaro.lol-anubis-auth=a.b.c",
	}
	for name, cookie := range cases {
		if _, code, _ := mintToken(t, w, cookie, w.g.own, origin); code != 403 {
			t.Errorf("%s: want 403, got %d", name, code)
		}
	}
}

func TestOnePassBuysAtMostN(t *testing.T) {
	w := newWorld(t, nil)
	cookie := anubisCookie(t, "pass-cap", "127.0.0.1", time.Now().Add(time.Hour), anubisPriv)
	for i := 0; i < 3; i++ {
		if _, code, msg := mintToken(t, w, cookie, w.g.own, origin); code != 200 {
			t.Fatalf("token %d: %d %s", i, code, msg)
		}
	}
	if _, code, _ := mintToken(t, w, cookie, w.g.own, origin); code != 429 {
		t.Fatalf("4th token: want 429, got %d", code)
	}
	if _, code, _ := mintToken(t, w, anubisCookie(t, "pass-other", "127.0.0.1", time.Now().Add(time.Hour), anubisPriv), w.g.own, origin); code != 200 {
		t.Fatal("a new pass should buy new tokens")
	}
}

func TestTokenForAnotherSiteIsRefused(t *testing.T) {
	w := newWorld(t, nil)
	tok, code, _ := mintToken(t, w, anubisCookie(t, "p2", "127.0.0.1", time.Now().Add(time.Hour), anubisPriv), w.g.own, "elsewhere.test")
	if code != 200 {
		t.Fatal("issue failed")
	}
	if code, body := get(t, w, auth(tok)); code != 401 || !strings.Contains(body, "another site") {
		t.Fatalf("got %d %q", code, body)
	}
}

func TestTamperedAndUntrustedTokensAreRefused(t *testing.T) {
	w := newWorld(t, nil)
	tok, _, _ := mintToken(t, w, anubisCookie(t, "p3", "127.0.0.1", time.Now().Add(time.Hour), anubisPriv), w.g.own, origin)
	bad := append([]byte{}, tok...)
	bad[10] ^= 1 // flip a nonce bit
	if code, body := get(t, w, auth(bad)); code != 401 || !strings.Contains(body, "does not verify") {
		t.Fatalf("tampered: %d %q", code, body)
	}
	// A token from an issuer the site does not trust (self-made key) is refused.
	stranger, _ := NewIssuer("stranger.test", &otherKey.PublicKey, true)
	nonce := make([]byte, 32)
	state, _ := type2.NewBasicPublicClient().CreateTokenRequest(stranger.Challenge(origin).Marshal(), nonce, stranger.KeyID, stranger.Key)
	sig, _ := type2.NewBasicPublicIssuer(otherKey).Evaluate(state.Request())
	ext, _ := state.FinalizeToken(sig)
	if code, body := get(t, w, auth(ext.Marshal())); code != 401 || !strings.Contains(body, "does not trust") {
		t.Fatalf("untrusted: %d %q", code, body)
	}
	if code, _ := get(t, w, map[string]string{"Authorization": "PrivateToken token=!!!"}); code != 401 {
		t.Fatal("garbage token accepted")
	}
}

func TestExternalIssuerTokenIsAccepted(t *testing.T) {
	ext, _ := NewIssuer("process-check.test", &otherKey.PublicKey, true)
	w := newWorld(t, func(c *Config) { c.External = []Issuer{ext} })
	nonce := make([]byte, 32)
	_, _ = rand.Read(nonce)
	state, _ := type2.NewBasicPublicClient().CreateTokenRequest(ext.Challenge(origin).Marshal(), nonce, ext.KeyID, ext.Key)
	sig, _ := type2.NewBasicPublicIssuer(otherKey).Evaluate(state.Request())
	tok, err := state.FinalizeToken(sig)
	if err != nil {
		t.Fatal(err)
	}
	if code, body := get(t, w, auth(tok.Marshal())); code != 200 || !strings.Contains(body, "privacy-pass") {
		t.Fatalf("got %d %q", code, body)
	}
}

func TestSpentLogSurvivesRestart(t *testing.T) {
	log := filepath.Join(t.TempDir(), "spent.log")
	w := newWorld(t, func(c *Config) { c.SpentLog = log })
	tok, _, _ := mintToken(t, w, anubisCookie(t, "p4", "127.0.0.1", time.Now().Add(time.Hour), anubisPriv), w.g.own, origin)
	if code, _ := get(t, w, auth(tok)); code != 200 {
		t.Fatal("first spend failed")
	}
	w2 := newWorld(t, func(c *Config) { c.SpentLog = log })
	if code, _ := get(t, w2, auth(tok)); code != 401 {
		t.Fatal("token spendable again after restart")
	}
}

func TestWebBotAuthPath(t *testing.T) {
	verdict := `{"outcome":"valid","testKey":false,"signatureAgent":{"uri":"https://agent.test/.well-known/http-message-signatures-directory"}}`
	var seen string
	verifier := httptest.NewServer(http.HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		b, _ := io.ReadAll(r.Body)
		seen = string(b)
		io.WriteString(rw, verdict)
	}))
	defer verifier.Close()
	w := newWorld(t, func(c *Config) { c.WBAVerifyURL = verifier.URL })
	signed := map[string]string{"Signature": "sig1=:AA==:", "Signature-Input": `sig1=("@authority");tag="web-bot-auth"`, "Signature-Agent": `sig1="https://agent.test"`}
	if code, body := get(t, w, signed); code != 200 || body != "backend; gate=web-bot-auth; agent=agent.test" {
		t.Fatalf("valid: %d %q", code, body)
	}
	if !strings.Contains(seen, `"signature-agent"`) || !strings.Contains(seen, `"url":"http://`) {
		t.Fatalf("verifier got %s", seen)
	}
	verdict = `{"outcome":"valid","testKey":true,"signatureAgent":{"uri":"https://x.test"}}`
	if _, body := get(t, w, signed); body != "anubis challenge page" {
		t.Fatalf("test key should not pass: %q", body)
	}
	verdict = `{"outcome":"invalid","category":"bad-signature"}`
	if _, body := get(t, w, signed); body != "anubis challenge page" {
		t.Fatalf("invalid should go to Anubis: %q", body)
	}
	// A client cannot forge the gate's own header.
	if _, body := get(t, w, map[string]string{GateHeader: "privacy-pass"}); body != "anubis challenge page" {
		t.Fatal("forged gate header passed")
	}
}
