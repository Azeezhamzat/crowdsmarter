import { lazy } from "react";
import { createBrowserRouter } from "react-router";

import { RouteAccessibility } from "./components/RouteAccessibility";
import { ProtectedRoute } from "./features/auth/ProtectedRoute";

const OrganisationAuditPage = lazy(() => import("./features/audit/OrganisationAuditPage").then((module) => ({ default: module.OrganisationAuditPage })));
const MyApplicationsPage = lazy(() => import("./features/applicants/MyApplicationsPage").then((module) => ({ default: module.MyApplicationsPage })));
const TrustPage = lazy(() => import("./features/trust/TrustPage").then((module) => ({ default: module.TrustPage })));
const DecisionAIReviewPage = lazy(() => import("./features/ai-assistance/DecisionAIReviewPage").then((module) => ({ default: module.DecisionAIReviewPage })));
const DecisionCollaborationPage = lazy(() => import("./features/collaboration/DecisionCollaborationPage").then((module) => ({ default: module.DecisionCollaborationPage })));
const OrganisationAnalyticsPage = lazy(() => import("./features/analytics/OrganisationAnalyticsPage").then((module) => ({ default: module.OrganisationAnalyticsPage })));
const AccountSettingsPage = lazy(() => import("./features/auth/AccountSettingsPage").then((module) => ({ default: module.AccountSettingsPage })));
const ForgotPasswordPage = lazy(() => import("./features/auth/ForgotPasswordPage").then((module) => ({ default: module.ForgotPasswordPage })));
const LoginPage = lazy(() => import("./features/auth/LoginPage").then((module) => ({ default: module.LoginPage })));
const SignupPage = lazy(() => import("./features/auth/SignupPage").then((module) => ({ default: module.SignupPage })));
const ResetPasswordPage = lazy(() => import("./features/auth/ResetPasswordPage").then((module) => ({ default: module.ResetPasswordPage })));
const VerifyEmailChangePage = lazy(() => import("./features/auth/VerifyEmailChangePage").then((module) => ({ default: module.VerifyEmailChangePage })));
const DecisionWorkspacePage = lazy(() => import("./features/decisions/DecisionWorkspacePage").then((module) => ({ default: module.DecisionWorkspacePage })));
const RequestDemoPage = lazy(() => import("./features/demo-request/RequestDemoPage").then((module) => ({ default: module.RequestDemoPage })));
const DecisionContributionsPage = lazy(() => import("./features/contributions/DecisionContributionsPage").then((module) => ({ default: module.DecisionContributionsPage })));
const MyContributionsPage = lazy(() => import("./features/contributions/MyContributionsPage").then((module) => ({ default: module.MyContributionsPage })));
const GuidedDecisionCreatePage = lazy(() => import("./features/decisions/GuidedDecisionCreatePage").then((module) => ({ default: module.GuidedDecisionCreatePage })));
const OrganisationExportPage = lazy(() => import("./features/exports/OrganisationExportPage").then((module) => ({ default: module.OrganisationExportPage })));
const OpenSessionOrganiserPage = lazy(() => import("./features/ideation/OpenSessionOrganiserPage").then((module) => ({ default: module.OpenSessionOrganiserPage })));
const OpenSessionPublicPage = lazy(() => import("./features/ideation/OpenSessionPublicPage").then((module) => ({ default: module.OpenSessionPublicPage })));
const OrganisationSessionsPage = lazy(() => import("./features/ideation/OrganisationSessionsPage").then((module) => ({ default: module.OrganisationSessionsPage })));
const DecisionEvaluationPage = lazy(() => import("./features/evaluations/DecisionEvaluationPage").then((module) => ({ default: module.DecisionEvaluationPage })));
const DecisionAnalysisPage = lazy(() => import("./features/decision-analysis/DecisionAnalysisPage").then((module) => ({ default: module.DecisionAnalysisPage })));
const OrganisationPrioritisationPage = lazy(() => import("./features/evaluations/OrganisationPrioritisationPage").then((module) => ({ default: module.OrganisationPrioritisationPage })));
const OrganisationForesightPage = lazy(() => import("./features/foresight/OrganisationForesightPage").then((module) => ({ default: module.OrganisationForesightPage })));
const ForesightCanvasesPage = lazy(() => import("./features/foresight/ForesightCanvasesPage").then((module) => ({ default: module.ForesightCanvasesPage })));
const ForesightCanvasPage = lazy(() => import("./features/foresight/ForesightCanvasPage").then((module) => ({ default: module.ForesightCanvasPage })));
const ForesightScenarioSetPage = lazy(() => import("./features/foresight/ForesightScenarioSetPage").then((module) => ({ default: module.ForesightScenarioSetPage })));
const DecisionGovernancePage = lazy(() => import("./features/governance/DecisionGovernancePage").then((module) => ({ default: module.DecisionGovernancePage })));
const AcceptInvitationPage = lazy(() => import("./features/invitations/AcceptInvitationPage").then((module) => ({ default: module.AcceptInvitationPage })));
const NotificationsPage = lazy(() => import("./features/notifications/NotificationsPage").then((module) => ({ default: module.NotificationsPage })));
const LandingPage = lazy(() => import("./features/landing/LandingPage").then((module) => ({ default: module.LandingPage })));
const NotFoundPage = lazy(() => import("./features/not-found/NotFoundPage").then((module) => ({ default: module.NotFoundPage })));
const OrganisationAdministrationPage = lazy(() => import("./features/organisations/OrganisationAdministrationPage").then((module) => ({ default: module.OrganisationAdministrationPage })));
const OrganisationDetailPage = lazy(() => import("./features/organisations/OrganisationDetailPage").then((module) => ({ default: module.OrganisationDetailPage })));
const OrganisationMethodsPage = lazy(() => import("./features/organisations/OrganisationMethodsPage").then((module) => ({ default: module.OrganisationMethodsPage })));
const OrganisationListPage = lazy(() => import("./features/organisations/OrganisationListPage").then((module) => ({ default: module.OrganisationListPage })));
const OrganisationPortfolioPage = lazy(() => import("./features/portfolio/OrganisationPortfolioPage").then((module) => ({ default: module.OrganisationPortfolioPage })));
const PlatformAdminPage = lazy(() => import("./features/platform-admin/PlatformAdminPage").then((module) => ({ default: module.PlatformAdminPage })));
const PlatformOrganisationSupportPage = lazy(() => import("./features/platform-admin/PlatformOrganisationSupportPage").then((module) => ({ default: module.PlatformOrganisationSupportPage })));
const DecisionOutcomesPage = lazy(() => import("./features/outcomes/DecisionOutcomesPage").then((module) => ({ default: module.DecisionOutcomesPage })));
const DecisionReasoningPage = lazy(() => import("./features/reasoning/DecisionReasoningPage").then((module) => ({ default: module.DecisionReasoningPage })));
const OrganisationSearchPage = lazy(() => import("./features/search/OrganisationSearchPage").then((module) => ({ default: module.OrganisationSearchPage })));
const WorkspaceDetailPage = lazy(() => import("./features/workspaces/WorkspaceDetailPage").then((module) => ({ default: module.WorkspaceDetailPage })));
const WorkspaceListPage = lazy(() => import("./features/workspaces/WorkspaceListPage").then((module) => ({ default: module.WorkspaceListPage })));

export const router = createBrowserRouter([
  {
    element: <RouteAccessibility />,
    children: [
      { path: "/", element: <LandingPage /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/signup", element: <SignupPage /> },
  { path: "/request-demo", element: <RequestDemoPage /> },
  { path: "/forgot-password", element: <ForgotPasswordPage /> },
  { path: "/reset-password", element: <ResetPasswordPage /> },
  { path: "/verify-email-change", element: <VerifyEmailChangePage /> },
  { path: "/accept-invitation", element: <AcceptInvitationPage /> },
  { path: "/s/:publicSlug", element: <OpenSessionPublicPage /> },
  { path: "/my-applications", element: <MyApplicationsPage /> },
  { path: "/trust", element: <TrustPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      { path: "/app", element: <OrganisationListPage /> },
      { path: "/notifications", element: <NotificationsPage /> },
      { path: "/contributions", element: <MyContributionsPage /> },
      { path: "/account", element: <AccountSettingsPage /> },
      { path: "/platform-admin", element: <PlatformAdminPage /> },
      { path: "/platform-admin/organisations/:organisationId", element: <PlatformOrganisationSupportPage /> },
      { path: "/organisations/:organisationId", element: <OrganisationDetailPage /> },
      { path: "/organisations/:organisationId/methods", element: <OrganisationMethodsPage /> },
      { path: "/organisations/:organisationId/administration", element: <OrganisationAdministrationPage /> },
      { path: "/organisations/:organisationId/workspaces", element: <WorkspaceListPage /> },
      { path: "/organisations/:organisationId/search", element: <OrganisationSearchPage /> },
      { path: "/organisations/:organisationId/analytics", element: <OrganisationAnalyticsPage /> },
      { path: "/organisations/:organisationId/portfolio", element: <OrganisationPortfolioPage /> },
      { path: "/organisations/:organisationId/sessions", element: <OrganisationSessionsPage /> },
      { path: "/organisations/:organisationId/sessions/:sessionId", element: <OpenSessionOrganiserPage /> },
      { path: "/organisations/:organisationId/prioritisation", element: <OrganisationPrioritisationPage /> },
      { path: "/organisations/:organisationId/export", element: <OrganisationExportPage /> },
      { path: "/organisations/:organisationId/foresight", element: <OrganisationForesightPage /> },
      { path: "/organisations/:organisationId/foresight/canvases", element: <ForesightCanvasesPage /> },
      { path: "/organisations/:organisationId/foresight/canvases/:canvasId", element: <ForesightCanvasPage /> },
      { path: "/organisations/:organisationId/foresight/canvases/:canvasId/scenarios/:scenarioSetId", element: <ForesightScenarioSetPage /> },
      { path: "/workspaces/:workspaceId", element: <WorkspaceDetailPage /> },
      { path: "/workspaces/:workspaceId/decisions/new", element: <GuidedDecisionCreatePage /> },
      { path: "/decisions/:decisionId", element: <DecisionWorkspacePage /> },
      { path: "/decisions/:decisionId/governance", element: <DecisionGovernancePage /> },
      { path: "/decisions/:decisionId/evaluations", element: <DecisionEvaluationPage /> },
      { path: "/decisions/:decisionId/analysis", element: <DecisionAnalysisPage /> },
      { path: "/decisions/:decisionId/outcomes", element: <DecisionOutcomesPage /> },
      { path: "/decisions/:decisionId/ai-review", element: <DecisionAIReviewPage /> },
      { path: "/decisions/:decisionId/collaboration", element: <DecisionCollaborationPage /> },
      { path: "/decisions/:decisionId/contributions", element: <DecisionContributionsPage /> },
      { path: "/organisations/:organisationId/audit", element: <OrganisationAuditPage /> },
      { path: "/decisions/:decisionId/reasoning/:section", element: <DecisionReasoningPage /> },
    ],
  },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
