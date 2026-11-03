// ppgate: Privacy Pass and Web Bot Auth front door for an unmodified Anubis. See package gate.
//
//	ppgate keygen   print a fresh Anubis signing seed and its public key, as .env lines
//	ppgate          serve (configuration from the environment, see README)
package main

import (
	"crypto/ed25519"
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"

	"captcharena.org/defence/ppgate/gate"
	"github.com/cloudflare/pat-go/util"
)

func env(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}

func must[T any](v T, err error) T {
	if err != nil {
		slog.Error("startup failed", "err", err)
		os.Exit(1)
	}
	return v
}

// issuerKey loads the RSA issuer key, creating a 2048-bit one on first start (RFC 9578 type 2 uses 2048-bit keys).
func issuerKey(path string) (*rsa.PrivateKey, error) {
	if data, err := os.ReadFile(path); err == nil {
		block, _ := pem.Decode(data)
		if block == nil {
			return nil, errors.New("issuer key file is not PEM")
		}
		k, err := x509.ParsePKCS8PrivateKey(block.Bytes)
		if err != nil {
			return nil, err
		}
		rk, ok := k.(*rsa.PrivateKey)
		if !ok {
			return nil, errors.New("issuer key is not RSA")
		}
		return rk, nil
	} else if !errors.Is(err, os.ErrNotExist) {
		return nil, err
	}
	k, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return nil, err
	}
	der, _ := x509.MarshalPKCS8PrivateKey(k)
	if err := os.WriteFile(path, pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: der}), 0o600); err != nil {
		return nil, err
	}
	slog.Info("created issuer key", "path", path)
	return k, nil
}

// externalIssuers reads TRUSTED_ISSUERS="name=https://host/.well-known/private-token-issuer-directory,..." and
// fetches each directory's type-2 token keys.
func externalIssuers(spec string, client *http.Client) []gate.Issuer {
	var out []gate.Issuer
	for _, item := range strings.Split(spec, ",") {
		name, dirURL, ok := strings.Cut(strings.TrimSpace(item), "=")
		if !ok {
			continue
		}
		res, err := client.Get(dirURL)
		if err != nil {
			slog.Warn("trusted issuer unreachable", "issuer", name, "err", err)
			continue
		}
		var dir struct {
			Keys []struct {
				Type int    `json:"token-type"`
				Key  string `json:"token-key"`
			} `json:"token-keys"`
		}
		err = json.NewDecoder(io.LimitReader(res.Body, 1<<16)).Decode(&dir)
		res.Body.Close()
		if err != nil {
			slog.Warn("trusted issuer directory unreadable", "issuer", name, "err", err)
			continue
		}
		for _, k := range dir.Keys {
			if k.Type != int(gate.TokenType) {
				continue
			}
			der, err := base64.RawURLEncoding.DecodeString(strings.TrimRight(k.Key, "="))
			if err != nil {
				der, err = base64.StdEncoding.DecodeString(k.Key)
			}
			if err != nil {
				continue
			}
			pub, err := util.UnmarshalTokenKey(der)
			if err != nil {
				slog.Warn("trusted issuer key unreadable", "issuer", name, "err", err)
				continue
			}
			is, err := gate.NewIssuer(name, pub, true)
			if err == nil {
				out = append(out, is)
				slog.Info("trusting issuer", "issuer", name, "key", is.KeyB64[:16]+"…")
			}
		}
	}
	return out
}

func main() {
	if len(os.Args) > 1 && os.Args[1] == "keygen" {
		pub, priv, _ := ed25519.GenerateKey(rand.Reader)
		fmt.Printf("ANUBIS_ED25519_PRIVATE_KEY_HEX=%s\nGATE_ANUBIS_PUBLIC_HEX=%s\n", hex.EncodeToString(priv.Seed()), hex.EncodeToString(pub))
		return
	}
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	slog.SetDefault(logger)
	pubHex := must(hex.DecodeString(env("GATE_ANUBIS_PUBLIC_HEX", "")))
	if len(pubHex) != ed25519.PublicKeySize {
		slog.Error("GATE_ANUBIS_PUBLIC_HEX must be a 32-byte hex Ed25519 public key")
		os.Exit(1)
	}
	perPass := must(strconv.Atoi(env("GATE_TOKENS_PER_PASS", "10")))
	client := &http.Client{Timeout: 5 * time.Second}
	g := must(gate.New(gate.Config{
		Origin:        env("GATE_ORIGIN", "localhost"),
		IssuerName:    env("GATE_ISSUER_NAME", env("GATE_ORIGIN", "localhost")),
		IssuerKey:     must(issuerKey(env("GATE_ISSUER_KEY_FILE", "/data/issuer-key.pem"))),
		External:      externalIssuers(env("GATE_TRUSTED_ISSUERS", ""), client),
		AnubisPub:     ed25519.PublicKey(pubHex),
		TokensPerPass: perPass,
		Anubis:        must(url.Parse(env("GATE_ANUBIS_URL", "http://anubis:8923"))),
		Backend:       must(url.Parse(env("GATE_BACKEND_URL", "http://backend:80"))),
		WBAVerifyURL:  env("GATE_WBA_VERIFY_URL", ""),
		AllowTestKeys: env("GATE_WBA_ALLOW_TEST_KEYS", "") == "1",
		SpentLog:      env("GATE_SPENT_LOG", "/data/spent.log"),
		RealIPHeader:  env("GATE_REAL_IP_HEADER", ""),
		Logger:        logger,
		HTTPClient:    client,
	}))
	mux := http.NewServeMux()
	mux.HandleFunc("/.well-known/ppgate-health", func(w http.ResponseWriter, _ *http.Request) { _, _ = io.WriteString(w, "ok\n") })
	mux.Handle("/", g)
	addr := env("GATE_LISTEN", ":8080")
	slog.Info("ppgate listening", "addr", addr)
	srv := &http.Server{Addr: addr, Handler: mux, ReadHeaderTimeout: 10 * time.Second}
	if err := srv.ListenAndServe(); err != nil {
		slog.Error("server stopped", "err", err)
		os.Exit(1)
	}
}
