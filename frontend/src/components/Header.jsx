import { useState } from "react";

const PREFIX_RE = /^[a-zA-Z0-9_-]{0,64}$/;

function Header({ prefix, onPrefixChange }) {
  const [quitting, setQuitting] = useState(false);
  const [localPrefix, setLocalPrefix] = useState(prefix ?? "");
  const [prefixError, setPrefixError] = useState(null);
  const [prefixSaved, setPrefixSaved] = useState(false);

  const handleQuit = async () => {
    if (!confirm("Quitter telephonIA ?")) return;
    setQuitting(true);
    try {
      await fetch("/api/shutdown", { method: "POST" });
    } catch {
      // Le serveur se coupe, la requete peut echouer — c'est normal
    }
  };

  const handlePrefixChange = (e) => {
    const value = e.target.value;
    setLocalPrefix(value);
    setPrefixSaved(false);
    if (!PREFIX_RE.test(value)) {
      setPrefixError("Caracteres autorises : a-z, A-Z, 0-9, _, -");
    } else {
      setPrefixError(null);
    }
  };

  const handlePrefixBlur = async () => {
    if (prefixError) return;
    const trimmed = localPrefix.trim();
    if (trimmed === (prefix ?? "")) return;
    try {
      await onPrefixChange(trimmed);
      setPrefixSaved(true);
      setTimeout(() => setPrefixSaved(false), 2000);
    } catch (err) {
      setPrefixError("Erreur : " + err.message);
    }
  };

  return (
    <div className="header">
      <button
        className="btn-quit"
        onClick={handleQuit}
        disabled={quitting}
        title="Quitter telephonIA"
      >
        {quitting ? "Arret..." : "Quitter"}
      </button>
      <h1>telephonIA</h1>
      <p>Generateur de bandes sonores SVI par IA</p>
      <div className="prefix-field">
        <label htmlFor="prefix-input">Identifiant du lot</label>
        <input
          id="prefix-input"
          type="text"
          value={localPrefix}
          onChange={handlePrefixChange}
          onBlur={handlePrefixBlur}
          placeholder="ex : mairie_cantine"
          maxLength={64}
          className={prefixError ? "prefix-input-error" : ""}
        />
        {prefixError && <span className="prefix-error">{prefixError}</span>}
        {prefixSaved && !prefixError && (
          <span className="prefix-saved">Enregistre</span>
        )}
        <p className="prefix-hint">
          Prefixe applique au nom des 3 fichiers WAV (ex :
          {" "}mairie_cantine_pre_decroche.wav). Laisser vide pour ne pas
          prefixer.
        </p>
      </div>
    </div>
  );
}

export default Header;
