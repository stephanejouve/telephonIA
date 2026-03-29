import { useState } from "react";

function Header() {
  const [quitting, setQuitting] = useState(false);

  const handleQuit = async () => {
    if (!confirm("Quitter telephonIA ?")) return;
    setQuitting(true);
    try {
      await fetch("/api/shutdown", { method: "POST" });
    } catch {
      // Le serveur se coupe, la requete peut echouer — c'est normal
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
    </div>
  );
}

export default Header;
