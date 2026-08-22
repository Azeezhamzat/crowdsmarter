import { createBrowserRouter } from "react-router";

import { RouteAccessibility } from "./components/RouteAccessibility";

import { OrganisationAuditPage } from "./features/audit/OrganisationAuditPage";
import { MyApplicationsPage } from "./features/applicants/MyApplicationsPage";
import { TrustPage } from "./features/trust/TrustPage";
import { DecisionAIReviewPage } from "./features/ai-assistance/DecisionAIReviewPage";
import { DecisionCollaborationPage } from "./features/collaboration/DecisionCollaborationPage";
import { OrganisationAnalyticsPage } from "./features/analytics/OrganisationAnalyticsPage";
import { AccountSettingsPage } from "./features/auth/AccountSettingsPage";
import { ForgotPasswordPage } from "./features/auth/ForgotPasswordPage";
import { LoginPage } from "./features/auth/LoginPage";
import { ResetPasswordPage } from "./features/auth/ResetPasswordPage";
import { ProtectedRoute } from "./features/auth/ProtectedRoute";
import { DecisionWorkspacePage } from "./features/decisions/DecisionWorkspacePage";
import { RequestDemoPage } from "./features/demo-request/RequestDemoPage";
import { DecisionContributionsPage } from "./features/contributions/DecisionContributionsPage";
import { MyContributionsPage } from "./features/contributions/MyContributionsPage";
import { GuidedDecisionCreatePage } from "./features/decisions/GuidedDecisionCreatePage";
import { OrganisationExportPage } from "./features/exports/OrganisationExportPage";
import { OpenSessionOrganiserPage } from "./features/ideation/OpenSessionOrganiserPage";
import { OpenSessionPublicPage } from "./features/ideation/OpenSessionPublicPage";
import { OrganisationSessionsPage } from "./features/ideation/OrganisationSessionsPage";
import { DecisionEvaluationPage } from "./features/evaluations/DecisionEvaluationPage";
import { DecisionAnalysisPage } from "./features/decision-analysis/DecisionAnalysisPage";
import { OrganisationPrioritisationPage } from "./features/evaluations/OrganisationPrioritisationPage";
import { OrganisationForesightPage } from "./features/foresight/OrganisationForesightPage";
import { ForesightCanvasesPage } from "./features/foresight/ForesightCanvasesPage";
import { ForesightCanvasPage } from "./features/foresight/ForesightCanvasPage";
import { ForesightScenarioSetPage } from "./features/foresight/ForesightScenarioSetPage";
import { DecisionGovernancePage } from "./features/governance/DecisionGovernancePage";
import { AcceptInvitationPage } from "./features/invitations/AcceptInvitationPage";
import { NotificationsPage } from "./features/notifications/NotificationsPage";
import { LandingPage } from "./features/landing/LandingPage";
import { NotFoundPage } from "./features/not-found/NotFoundPage";
import { OrganisationAdministrationPage } from "./features/organisations/OrganisationAdministrationPage";
import { OrganisationDetailPage } from "./features/organisations/OrganisationDetailPage";
import { OrganisationMethodsPage } from "./features/organisations/OrganisationMethodsPage";
import { OrganisationListPage } from "./features/organisations/OrganisationListPage";
import { OrganisationPortfolioPage } from "./features/portfolio/OrganisationPortfolioPage";
import { PlatformAdminPage } from "./features/platform-admin/PlatformAdminPage";
import { PlatformOrganisationSupportPage } from "./features/platform-admin/PlatformOrganisationSupportPage";
import { DecisionOutcomesPage } from "./features/outcomes/DecisionOutcomesPage";
import { DecisionReasoningPage } from "./features/reasoning/DecisionReasoningPage";
import { OrganisationSearchPage } from "./features/search/OrganisationSearchPage";
import { WorkspaceDetailPage } from "./features/workspaces/WorkspaceDetailPage";
import { WorkspaceListPage } from "./features/workspaces/WorkspaceListPage";

export const router = createBrowserRouter([
  {
    element: <RouteAccessibility />,
    children: [
      { path: "/", element: <LandingPage /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/request-demo", element: <RequestDemoPage /> },
  { path: "/forgot-password", element: <ForgotPasswordPage /> },
  { path: "/reset-password", element: <ResetPasswordPage /> },
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
