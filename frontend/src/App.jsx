import { useEffect, useState } from "react";
import FAQ from "./components/FAQ";
import GenerateButton from "./components/GenerateButton";
import Header from "./components/Header";
import MessageCard from "./components/MessageCard";
import MusicUpload from "./components/MusicUpload";
import VoiceSelector from "./components/VoiceSelector";

function App() {
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const [audioVersion, setAudioVersion] = useState(0);
  const [serverDown, setServerDown] = useState(false);
  const [prefix, setPrefix] = useState("");
  const [showFAQ, setShowFAQ] = useState(false);

  const fetchMessages = async () => {
    try {
      const res = await fetch("/api/messages");
      if (!res.ok) throw new Error(`Erreur ${res.status}`);
      const data = await res.json();
      setMessages(data);
      setError(null);
    } catch (err) {
      setError("Impossible de charger les messages : " + err.message);
    }
  };

  const fetchPrefix = async () => {
    try {
      const res = await fetch("/api/prefix");
      if (!res.ok) return;
      const data = await res.json();
      setPrefix(data.prefix ?? "");
    } catch {
      // silencieux : endpoint optionnel
    }
  };

  const savePrefix = async (newPrefix) => {
    const res = await fetch("/api/prefix", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prefix: newPrefix }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || `Erreur ${res.status}`);
    }
    const data = await res.json();
    setPrefix(data.prefix ?? "");
    await fetchMessages();
    setAudioVersion((v) => v + 1);
    return data.prefix ?? "";
  };

  useEffect(() => {
    fetchMessages();
    fetchPrefix();
  }, []);

  // Health check : detecter l'arret du serveur
  useEffect(() => {
    let failures = 0;
    const interval = setInterval(async () => {
      try {
        const res = await fetch("/api/health");
        if (res.ok) failures = 0;
        else failures++;
      } catch {
        failures++;
      }
      if (failures >= 2) {
        setServerDown(true);
        clearInterval(interval);
      }
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleSave = async (name, text) => {
    const res = await fetch(`/api/messages/${name}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error(`Erreur ${res.status}`);
    const updated = await res.json();
    setMessages((prev) =>
      prev.map((m) => (m.name === name ? updated : m))
    );
  };

  const handleAudioImport = () => {
    setAudioVersion((v) => v + 1);
    fetchMessages();
  };

  const handleAudioDelete = () => {
    fetchMessages();
  };

  const handleGenerate = async () => {
    // Alerte si l'identifiant de lot est vide : demander une racine generique
    if (!prefix) {
      const entered = window.prompt(
        "Choisir une racine generique pour les 3 fichiers WAV.\n" +
          "Exemple : mairie_cantine (produira mairie_cantine_pre_decroche.wav, etc.)\n\n" +
          "Laisser vide et valider pour generer sans prefixe.",
        "mairie_cantine"
      );
      if (entered === null) return null; // annulation
      const cleaned = entered.trim();
      if (cleaned && !/^[a-zA-Z0-9_-]{0,64}$/.test(cleaned)) {
        window.alert(
          "Prefixe invalide. Caracteres autorises : a-z, A-Z, 0-9, _, - (64 max)"
        );
        return null;
      }
      try {
        await savePrefix(cleaned);
      } catch (err) {
        window.alert("Impossible d'enregistrer le prefixe : " + err.message);
        return null;
      }
    }

    const imported = messages.filter((m) => m.imported_g729);
    if (imported.length > 0) {
      const names = imported.map((m) => m.label).join(", ");
      const ok = window.confirm(
        `${names} : audio importe (G.729) qui sera ecrase par la generation TTS.\n\nContinuer ?`
      );
      if (!ok) return null;
    }

    const res = await fetch("/api/generate", { method: "POST" });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(detail);
    }
    const data = await res.json();
    setAudioVersion((v) => v + 1);
    await fetchMessages();
    return data;
  };

  if (serverDown) {
    return (
      <div className="shutdown-screen">
        <div className="shutdown-card">
          <h1>telephonIA</h1>
          <p>L'application a ete fermee.</p>
          <p className="shutdown-hint">Vous pouvez fermer cet onglet.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <Header prefix={prefix} onPrefixChange={savePrefix} onOpenFAQ={() => setShowFAQ(true)} />
      {showFAQ && <FAQ onClose={() => setShowFAQ(false)} />}
      {error && <div className="error-banner">{error}</div>}
      {messages.map((msg) => (
        <MessageCard
          key={msg.name}
          message={msg}
          audioVersion={audioVersion}
          prefix={prefix}
          onSave={handleSave}
          onAudioImport={handleAudioImport}
          onAudioDelete={handleAudioDelete}
        />
      ))}
      <MusicUpload />
      <VoiceSelector />
      {messages.length > 0 && (
        <GenerateButton onGenerate={handleGenerate} />
      )}
    </div>
  );
}

export default App;
