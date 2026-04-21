import { useState } from "react";

const FAQ_ITEMS = [
  {
    q: "Qu'est-ce que telephonIA ?",
    a: "telephonIA est un generateur de bandes sonores pour serveurs vocaux interactifs (SVI). Il produit 3 fichiers WAV (pre-decroche, attente, dissuasion) a partir de textes que vous redigez, en utilisant la synthese vocale par IA.",
  },
  {
    q: "Comment changer la voix ?",
    a: "Utilisez le selecteur \"Voix\" en bas de page. Vous pouvez choisir parmi les voix disponibles (ElevenLabs ou Edge TTS selon la configuration). Le changement s'applique a la prochaine generation.",
  },
  {
    q: "Quels formats audio pour l'import ?",
    a: "Vous pouvez importer des fichiers WAV ou G.729 (.wav). L'import remplace la synthese vocale pour le message concerne. Lors de la generation, les messages importes ne sont pas re-synthetises sauf si vous confirmez l'ecrasement.",
  },
  {
    q: "Le mixage musique de fond, comment ca marche ?",
    a: "Uploadez un fichier audio via la section \"Musique de fond\". La musique sera mixee automatiquement avec le message d'attente lors de la generation. Formats acceptes : MP3, WAV, OGG.",
  },
  {
    q: "Peut-on importer un audio au lieu du TTS ?",
    a: "Oui. Chaque message dispose d'un bouton \"Importer audio\". L'audio importe sera utilise tel quel a la place de la synthese vocale. Vous pouvez le supprimer pour revenir au TTS.",
  },
  {
    q: "Quel est le format de sortie ?",
    a: "Les fichiers generes sont au format WAV, prets a etre deployes sur un serveur telephonique (IPBX, Asterisk, etc.). Chaque fichier peut etre telecharge individuellement.",
  },
  {
    q: "Comment changer la musique de fond ?",
    a: "Dans la section \"Musique de fond\", supprimez la musique actuelle puis uploadez un nouveau fichier. La nouvelle musique sera utilisee lors de la prochaine generation.",
  },
  {
    q: "A quoi sert le prefixe de fichier ?",
    a: "Le prefixe (identifiant du lot) est ajoute au debut du nom des fichiers generes. Par exemple, avec le prefixe \"mairie_cantine\", les fichiers seront nommes mairie_cantine_pre_decroche.wav, etc. Il permet d'organiser vos lots de fichiers.",
  },
];

function FAQ({ onClose }) {
  const [openIndex, setOpenIndex] = useState(null);

  const toggle = (i) => {
    setOpenIndex(openIndex === i ? null : i);
  };

  return (
    <div className="faq-overlay" onClick={onClose}>
      <div className="faq-modal" onClick={(e) => e.stopPropagation()}>
        <button className="faq-close" onClick={onClose} title="Fermer">
          &times;
        </button>
        <h2 className="faq-title">Questions frequentes</h2>
        <div className="faq-list">
          {FAQ_ITEMS.map((item, i) => (
            <div
              key={i}
              className={"faq-item" + (openIndex === i ? " faq-item-open" : "")}
            >
              <button className="faq-question" onClick={() => toggle(i)}>
                <span>{item.q}</span>
                <span className="faq-chevron">{openIndex === i ? "−" : "+"}</span>
              </button>
              {openIndex === i && (
                <div className="faq-answer">{item.a}</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default FAQ;
