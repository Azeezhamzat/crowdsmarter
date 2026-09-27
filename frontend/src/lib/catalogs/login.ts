import { defineCatalog } from "../i18n";

/**
 * French and Arabic strings are AI-assisted and have not been reviewed
 * by a native speaker - see docs/i18n.md before treating them as final copy.
 */
export const loginCatalog = defineCatalog({
  en: {
    welcomeEyebrow: "Welcome back",
    heading: "Continue the reasoning, not just the record.",
    signInHeading: "Sign in to CrowdSmarter",
    signInHint: "Use the email address associated with your organisation invitation.",
    emailLabel: "Email address",
    passwordLabel: "Password",
    forgotPassword: "Forgot password?",
    signInButton: "Sign in securely",
    signingInButton: "Signing in securely…",
    requestDemo: "Discuss a decision",
  },
  fr: {
    welcomeEyebrow: "Content de vous revoir",
    heading: "Poursuivez le raisonnement, pas seulement le dossier.",
    signInHeading: "Se connecter à CrowdSmarter",
    signInHint: "Utilisez l'adresse e-mail associée à l'invitation de votre organisation.",
    emailLabel: "Adresse e-mail",
    passwordLabel: "Mot de passe",
    forgotPassword: "Mot de passe oublié ?",
    signInButton: "Se connecter en toute sécurité",
    signingInButton: "Connexion sécurisée en cours…",
    requestDemo: "Parler d'une décision",
  },
  ar: {
    welcomeEyebrow: "مرحباً بعودتك",
    heading: "واصل التفكير، لا مجرد حفظ السجل.",
    signInHeading: "تسجيل الدخول إلى CrowdSmarter",
    signInHint: "استخدم عنوان البريد الإلكتروني المرتبط بدعوة مؤسستك.",
    emailLabel: "عنوان البريد الإلكتروني",
    passwordLabel: "كلمة المرور",
    forgotPassword: "هل نسيت كلمة المرور؟",
    signInButton: "تسجيل الدخول بأمان",
    signingInButton: "جارٍ تسجيل الدخول بأمان…",
    requestDemo: "ناقش قراراً",
  },
});
