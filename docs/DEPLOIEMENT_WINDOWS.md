# Deploiement telephonIA sur Windows 11

Scenario : PC Windows 11 d'entreprise, rien installe, pare-feu potentiellement restrictif.

---

## 1. Construire le .exe

Le .exe se construit **en CI** (GitHub Actions) — pas besoin d'installer quoi
que ce soit sur le PC cible.

### Declenchement automatique (tag)

```bash
git tag v0.2.0
git push origin v0.2.0
```

Le workflow `build-windows.yml` se declenche, construit le .exe sur un runner
Windows, et le publie comme artefact telechargeable.

### Declenchement manuel

Sur GitHub → onglet **Actions** → workflow **Build Windows** → bouton
**Run workflow**.

### Recuperer le .exe

1. Aller sur GitHub → **Actions** → dernier run du workflow **Build Windows**
2. En bas de la page, section **Artifacts** → telecharger `telephonIA-windows`
3. Dezipper → `telephonIA.exe` (~80-120 Mo)

---

## 2. Installer sur le PC Windows

### Ce qu'il faut

- Le fichier `telephonIA.exe` (sur cle USB ou partage reseau)
- Le fichier `musique_fond.mp3` (optionnel, pour le message d'attente)

### Procedure

1. Creer un dossier sur le PC, par exemple :
   ```
   C:\telephonIA\
   ```

2. Copier `telephonIA.exe` dans ce dossier

3. Creer un sous-dossier `assets\` et y copier `musique_fond.mp3` :
   ```
   C:\telephonIA\
       telephonIA.exe
       assets\
           musique_fond.mp3
   ```

4. Double-cliquer sur `telephonIA.exe`

5. Windows Defender va probablement afficher un avertissement
   ("Application non reconnue") :
   - Cliquer **Informations complementaires**
   - Cliquer **Executer quand meme**

6. Le navigateur s'ouvre automatiquement sur l'interface web

7. Les fichiers WAV generes apparaissent dans `C:\telephonIA\output\`

---

## 3. Pare-feu — ports et domaines requis

telephonIA utilise **Edge TTS** (Microsoft) qui necessite un acces Internet
sortant. Si le pare-feu bloque les connexions, la generation echouera.

### Ports

| Port | Protocole | Usage |
|------|-----------|-------|
| 443  | HTTPS     | API REST Edge TTS |
| 443  | WSS       | WebSocket streaming audio |

### Domaines a autoriser

```
speech.platform.bing.com
*.tts.speech.microsoft.com
```

### Comment tester

Depuis le PC Windows, ouvrir PowerShell :

```powershell
# Test connexion Edge TTS
Invoke-WebRequest -Uri "https://speech.platform.bing.com" -Method Head -TimeoutSec 5
```

- **Reponse 200 ou 404** → le pare-feu laisse passer, tout va fonctionner
- **Timeout ou erreur connexion** → le pare-feu bloque, voir section suivante

### Si le pare-feu bloque

Options par ordre de preference :

1. **Demander l'ouverture** des domaines ci-dessus au service IT
   (argument : ce sont des services Microsoft officiels, meme infra que
   Cortana / Windows Narrator / Azure Cognitive Services)

2. **Utiliser un proxy** — si le PC passe par un proxy HTTP :
   ```powershell
   # Avant de lancer telephonIA :
   $env:HTTP_PROXY = "http://proxy.entreprise.local:8080"
   $env:HTTPS_PROXY = "http://proxy.entreprise.local:8080"
   .\telephonIA.exe
   ```

3. **ElevenLabs au lieu d'Edge TTS** — si `api.elevenlabs.io` est autorise
   mais pas les domaines Microsoft :
   ```powershell
   # Stocker la cle API (une seule fois)
   pip install keyring
   keyring set elevenlabs_api_key telephonia
   ```
   > Note : necessite Python installe pour la commande keyring.
   > Alternative : ajouter manuellement dans le Windows Credential Manager :
   > - Ouvrir **Gestionnaire d'identification** (credential manager)
   > - Ajouter une **identification generique**
   > - Service : `elevenlabs_api_key`
   > - Nom d'utilisateur : `telephonia`
   > - Mot de passe : votre cle API

---

## 4. Checklist deploiement

```
[ ] telephonIA.exe copie sur le PC
[ ] Dossier assets/musique_fond.mp3 en place (optionnel)
[ ] Test pare-feu : speech.platform.bing.com accessible
[ ] Premier lancement : Windows Defender autorise
[ ] Generation d'un message test → fichier WAV dans output/
[ ] Ecoute du WAV : voix correcte, musique de fond OK
```

---

## Troubleshooting

| Symptome | Cause probable | Solution |
|----------|---------------|----------|
| .exe ne se lance pas | Windows Defender / SmartScreen | "Informations complementaires" → "Executer quand meme" |
| .exe bloque par antivirus | Antivirus entreprise (Symantec, etc.) | Ajouter une exception pour le dossier `C:\telephonIA\` |
| "Connexion impossible" a la generation | Pare-feu bloque Edge TTS | Voir section 3 |
| Interface web ne s'ouvre pas | Pas de navigateur par defaut | Ouvrir manuellement l'URL affichee dans la console |
| Pas de musique de fond | `musique_fond.mp3` absent | Placer le fichier dans `assets\` a cote du .exe |
| Son metallique / coupe | Fichier source MP3 de mauvaise qualite | Utiliser un MP3 >= 128 kbps |
| "Rate limit" ElevenLabs | Quota mensuel atteint | Ne pas configurer de cle → bascule auto sur Edge TTS |
