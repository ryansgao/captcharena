// ppclient: the agent side of the gate. Learns the challenge from the site's WWW-Authenticate header, fetches
// blind-signed tokens from an issuer (RFC 9578 type 2), and spends one per request (RFC 9577).
//
//	ppclient fetch -site URL -issuer URL [-cookie 'name=value'] [-n 5] [-tokens tokens.json]
//	ppclient get   -site URL [-path /] [-tokens tokens.json] [-token-index i]   (spend one token)
package main

import (
	"bytes"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"regexp"
	"strings"
	"time"

	"github.com/cloudflare/pat-go/tokens"
	"github.com/cloudflare/pat-go/tokens/type2"
	"github.com/cloudflare/pat-go/util"
)

var client = &http.Client{Timeout: 15 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}

type challenge struct {
	raw      []byte
	parsed   tokens.TokenChallenge
	tokenKey []byte
}

var challengeRe = regexp.MustCompile(`PrivateToken\s+challenge="([^"]+)",\s*token-key="([^"]+)"`)

func b64(s string) ([]byte, error) {
	return base64.RawURLEncoding.DecodeString(strings.TrimRight(s, "="))
}

// challenges reads every PrivateToken challenge the site offers.
func challenges(site string) ([]challenge, error) {
	res, err := client.Get(site)
	if err != nil {
		return nil, err
	}
	res.Body.Close()
	var out []challenge
	for _, m := range challengeRe.FindAllStringSubmatch(strings.Join(res.Header.Values("WWW-Authenticate"), ", "), -1) {
		raw, err1 := b64(m[1])
		key, err2 := b64(m[2])
		if err1 != nil || err2 != nil {
			continue
		}
		c, err := tokens.UnmarshalTokenChallenge(raw)
		if err != nil {
			continue
		}
		out = append(out, challenge{raw: raw, parsed: c, tokenKey: key})
	}
	if len(out) == 0 {
		return nil, errors.New("site sent no PrivateToken challenge")
	}
	return out, nil
}

func fetch(site, issuer, cookie string, n int, path string) error {
	chs, err := challenges(site)
	if err != nil {
		return err
	}
	res, err := client.Get(strings.TrimRight(issuer, "/") + "/.well-known/private-token-issuer-directory")
	if err != nil {
		return err
	}
	var dir struct {
		URI  string `json:"issuer-request-uri"`
		Keys []struct {
			Type int    `json:"token-type"`
			Key  string `json:"token-key"`
		} `json:"token-keys"`
	}
	err = json.NewDecoder(res.Body).Decode(&dir)
	res.Body.Close()
	if err != nil || len(dir.Keys) == 0 {
		return fmt.Errorf("issuer directory unreadable: %v", err)
	}
	keyDER, err := b64(dir.Keys[0].Key)
	if err != nil {
		return err
	}
	var ch *challenge
	for i := range chs {
		if bytes.Equal(chs[i].tokenKey, keyDER) {
			ch = &chs[i]
		}
	}
	if ch == nil {
		return errors.New("the site does not offer a challenge for this issuer's key")
	}
	pub, err := util.UnmarshalTokenKey(keyDER)
	if err != nil {
		return err
	}
	id := sha256.Sum256(keyDER)
	keyID := id[:]
	reqURL := dir.URI
	if strings.HasPrefix(reqURL, "/") {
		reqURL = strings.TrimRight(issuer, "/") + reqURL
	}
	var store []string
	if data, err := os.ReadFile(path); err == nil {
		_ = json.Unmarshal(data, &store)
	}
	got := 0
	for i := 0; i < n; i++ {
		nonce := make([]byte, 32)
		_, _ = rand.Read(nonce)
		state, err := type2.NewBasicPublicClient().CreateTokenRequest(ch.raw, nonce, keyID, pub)
		if err != nil {
			return err
		}
		req, _ := http.NewRequest(http.MethodPost, reqURL, bytes.NewReader(state.Request().Marshal()))
		req.Header.Set("Content-Type", "application/private-token-request")
		if cookie != "" {
			req.Header.Set("Cookie", cookie)
		}
		res, err := client.Do(req)
		if err != nil {
			return err
		}
		body, _ := io.ReadAll(io.LimitReader(res.Body, 4096))
		res.Body.Close()
		if res.StatusCode != http.StatusOK {
			fmt.Printf("token %d refused: HTTP %d %s", i+1, res.StatusCode, body)
			break
		}
		tok, err := state.FinalizeToken(body)
		if err != nil {
			return fmt.Errorf("issuer returned a bad blind signature: %w", err)
		}
		store = append(store, base64.RawURLEncoding.EncodeToString(tok.Marshal()))
		got++
	}
	data, _ := json.MarshalIndent(store, "", " ")
	if err := os.WriteFile(path, data, 0o600); err != nil {
		return err
	}
	fmt.Printf("fetched %d token(s); %d stored in %s\n", got, len(store), path)
	return nil
}

func get(site, path, store string, index int) error {
	var toks []string
	data, err := os.ReadFile(store)
	if err == nil {
		_ = json.Unmarshal(data, &toks)
	}
	if len(toks) == 0 {
		return errors.New("no tokens left")
	}
	if index < 0 || index >= len(toks) {
		index = 0
	}
	tok := toks[index]
	if index == 0 {
		toks = toks[1:] // spent; -token-index lets a test resend one on purpose
	}
	req, _ := http.NewRequest(http.MethodGet, strings.TrimRight(site, "/")+path, nil)
	req.Header.Set("Authorization", fmt.Sprintf(`PrivateToken token="%s"`, tok))
	res, err := client.Do(req)
	if err != nil {
		return err
	}
	body, _ := io.ReadAll(io.LimitReader(res.Body, 2048))
	res.Body.Close()
	out, _ := json.MarshalIndent(toks, "", " ")
	_ = os.WriteFile(store, out, 0o600)
	fmt.Printf("HTTP %d\n%s\n", res.StatusCode, body)
	return nil
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: ppclient fetch|get [flags]")
		os.Exit(2)
	}
	fs := flag.NewFlagSet(os.Args[1], flag.ExitOnError)
	site := fs.String("site", "http://localhost:8330/", "protected site")
	issuer := fs.String("issuer", "", "issuer base URL (default: the site)")
	cookie := fs.String("cookie", "", "Cookie header proving an Anubis pass (fetch)")
	n := fs.Int("n", 5, "tokens to fetch")
	path := fs.String("path", "/", "path to request (get)")
	store := fs.String("tokens", "tokens.json", "token store")
	index := fs.Int("token-index", 0, "which stored token to spend (get)")
	_ = fs.Parse(os.Args[2:])
	if *issuer == "" {
		*issuer = *site
	}
	var err error
	switch os.Args[1] {
	case "fetch":
		err = fetch(*site, *issuer, *cookie, *n, *store)
	case "get":
		err = get(*site, *path, *store, *index)
	default:
		err = errors.New("unknown command")
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, "ppclient:", err)
		os.Exit(1)
	}
}
