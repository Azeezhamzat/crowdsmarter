import { defineCatalog } from "../i18n";

/**
 * French and Portuguese strings are AI-assisted and have not been reviewed
 * by a native speaker - see docs/i18n.md before treating them as final copy.
 */
export const openSessionCatalog = defineCatalog({
  en: {
    joinHeading: "Join to submit an idea and vote",
    joinDescription: "Just your name and email — no account or password needed.",
    nameLabel: "Name",
    emailLabel: "Email",
    joinButton: "Join session",
    joiningButton: "Joining…",
  },
  fr: {
    joinHeading: "Rejoignez pour soumettre une idée et voter",
    joinDescription: "Juste votre nom et votre e-mail — aucun compte ni mot de passe requis.",
    nameLabel: "Nom",
    emailLabel: "E-mail",
    joinButton: "Rejoindre la session",
    joiningButton: "Connexion en cours…",
  },
  pt: {
    joinHeading: "Junte-se para enviar uma ideia e votar",
    joinDescription: "Apenas o seu nome e e-mail — sem conta nem palavra-passe necessária.",
    nameLabel: "Nome",
    emailLabel: "E-mail",
    joinButton: "Juntar-se à sessão",
    joiningButton: "A entrar…",
  },
});
