"""Thin REST endpoints for Phase 14 collective evaluation and prioritisation."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.decisions.selectors import decision_for_user
from apps.organisations.models import Organisation

from .selectors import (candidate_for_user, exercise_for_user, exercise_workspace_for_user, exercises_for_decision, portfolio_for_user, portfolios_for_organisation, round_for_user)
from .serializers import (EvaluationCriterionSerializer, EvaluationCriterionWriteSerializer, EvaluationExercisePatchSerializer, EvaluationExerciseSerializer, EvaluationExerciseWriteSerializer, EvaluationRoundSerializer, EvaluationRoundTransitionSerializer, EvaluationRoundWriteSerializer, EvaluationScoringOptionSerializer, EvaluationSubmissionSerializer, EvaluationSubmissionWriteSerializer, MinorityReportSerializer, MinorityReportWriteSerializer, PortfolioAssessmentSerializer, PortfolioAssessmentWriteSerializer, PortfolioCandidateSerializer, PortfolioCandidateWriteSerializer, PortfolioCriterionSerializer, PortfolioCriterionWriteSerializer, PortfolioSelectionSerializer, PortfolioSelectionWriteSerializer, PrioritisationPortfolioPatchSerializer, PrioritisationPortfolioSerializer, PrioritisationPortfolioWriteSerializer)
from .services import (add_candidate, add_portfolio_criterion, create_criterion, create_exercise, create_minority_report, create_portfolio, create_round, evaluation_results, save_portfolio_assessment, save_submission, scoring_options_for_exercise, set_selection, transition_round, update_exercise, update_portfolio)


class EvaluationExerciseListCreateView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,decision_id):
        items=exercises_for_decision(user=request.user,decision_id=decision_id)
        return Response(EvaluationExerciseSerializer(items,many=True,context={"request":request}).data)
    def post(self,request,decision_id):
        decision=decision_for_user(user=request.user,decision_id=decision_id)
        serializer=EvaluationExerciseWriteSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        item=create_exercise(actor=request.user,decision=decision,**serializer.validated_data)
        return Response(EvaluationExerciseSerializer(item,context={"request":request}).data,status=status.HTTP_201_CREATED)


class EvaluationExerciseDetailView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,exercise_id):
        item=exercise_workspace_for_user(user=request.user,exercise_id=exercise_id)
        return Response(EvaluationExerciseSerializer(item,context={"request":request}).data)
    def patch(self,request,exercise_id):
        item=exercise_for_user(user=request.user,exercise_id=exercise_id)
        serializer=EvaluationExercisePatchSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        item=update_exercise(actor=request.user,exercise=item,fields=dict(serializer.validated_data))
        return Response(EvaluationExerciseSerializer(item,context={"request":request}).data)


class EvaluationScoringOptionsView(APIView):
    """Active options for the submission form — blinded to 'Application N' when the exercise asks for it."""
    permission_classes=[IsAuthenticated]
    def get(self,request,exercise_id):
        exercise=exercise_for_user(user=request.user,exercise_id=exercise_id)
        rows=scoring_options_for_exercise(exercise=exercise,viewer=request.user)
        return Response(EvaluationScoringOptionSerializer(rows,many=True).data)


class EvaluationCriterionCreateView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,exercise_id):
        exercise=exercise_for_user(user=request.user,exercise_id=exercise_id)
        serializer=EvaluationCriterionWriteSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        item=create_criterion(actor=request.user,exercise=exercise,**serializer.validated_data)
        return Response(EvaluationCriterionSerializer(item).data,status=status.HTTP_201_CREATED)


class EvaluationRoundCreateView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,exercise_id):
        exercise=exercise_for_user(user=request.user,exercise_id=exercise_id)
        serializer=EvaluationRoundWriteSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        item=create_round(actor=request.user,exercise=exercise,**serializer.validated_data)
        return Response(EvaluationRoundSerializer(item,context={"request":request}).data,status=status.HTTP_201_CREATED)


class EvaluationRoundTransitionView(APIView):
    permission_classes=[IsAuthenticated]
    def patch(self,request,round_id):
        item=round_for_user(user=request.user,round_id=round_id)
        serializer=EvaluationRoundTransitionSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        item=transition_round(actor=request.user,round=item,**serializer.validated_data)
        return Response(EvaluationRoundSerializer(item,context={"request":request}).data)


class EvaluationSubmissionView(APIView):
    permission_classes=[IsAuthenticated]
    def put(self,request,round_id):
        item=round_for_user(user=request.user,round_id=round_id)
        serializer=EvaluationSubmissionWriteSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        submission=save_submission(actor=request.user,round=item,**serializer.validated_data)
        return Response(EvaluationSubmissionSerializer(submission,context={"request":request}).data)


class EvaluationResultsView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,round_id):
        item=round_for_user(user=request.user,round_id=round_id)
        return Response(evaluation_results(round=item,viewer=request.user))


class MinorityReportCreateView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,exercise_id):
        exercise=exercise_for_user(user=request.user,exercise_id=exercise_id)
        serializer=MinorityReportWriteSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        item=create_minority_report(actor=request.user,exercise=exercise,**serializer.validated_data)
        return Response(MinorityReportSerializer(item).data,status=status.HTTP_201_CREATED)


class PrioritisationPortfolioListCreateView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,organisation_id):
        items=portfolios_for_organisation(user=request.user,organisation_id=organisation_id)
        return Response(PrioritisationPortfolioSerializer(items,many=True,context={"request":request}).data)
    def post(self,request,organisation_id):
        organisation=get_object_or_404(Organisation.objects.for_user(request.user),id=organisation_id)
        serializer=PrioritisationPortfolioWriteSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        item=create_portfolio(actor=request.user,organisation=organisation,**serializer.validated_data)
        return Response(PrioritisationPortfolioSerializer(item,context={"request":request}).data,status=status.HTTP_201_CREATED)


class PrioritisationPortfolioDetailView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,portfolio_id):
        item=portfolio_for_user(user=request.user,portfolio_id=portfolio_id)
        return Response(PrioritisationPortfolioSerializer(item,context={"request":request}).data)
    def patch(self,request,portfolio_id):
        item=portfolio_for_user(user=request.user,portfolio_id=portfolio_id)
        serializer=PrioritisationPortfolioPatchSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        item=update_portfolio(actor=request.user,portfolio=item,fields=dict(serializer.validated_data))
        return Response(PrioritisationPortfolioSerializer(item,context={"request":request}).data)


class PortfolioCriterionCreateView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,portfolio_id):
        portfolio=portfolio_for_user(user=request.user,portfolio_id=portfolio_id)
        serializer=PortfolioCriterionWriteSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        item=add_portfolio_criterion(actor=request.user,portfolio=portfolio,**serializer.validated_data)
        return Response(PortfolioCriterionSerializer(item).data,status=status.HTTP_201_CREATED)


class PortfolioCandidateCreateView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,portfolio_id):
        portfolio=portfolio_for_user(user=request.user,portfolio_id=portfolio_id)
        serializer=PortfolioCandidateWriteSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        item=add_candidate(actor=request.user,portfolio=portfolio,**serializer.validated_data)
        return Response(PortfolioCandidateSerializer(item,context={"request":request}).data,status=status.HTTP_201_CREATED)


class PortfolioAssessmentView(APIView):
    permission_classes=[IsAuthenticated]
    def put(self,request,candidate_id):
        candidate=candidate_for_user(user=request.user,candidate_id=candidate_id)
        serializer=PortfolioAssessmentWriteSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        item=save_portfolio_assessment(actor=request.user,candidate=candidate,**serializer.validated_data)
        return Response(PortfolioAssessmentSerializer(item,context={"request":request}).data)


class PortfolioSelectionView(APIView):
    permission_classes=[IsAuthenticated]
    def put(self,request,candidate_id):
        candidate=candidate_for_user(user=request.user,candidate_id=candidate_id)
        serializer=PortfolioSelectionWriteSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        item=set_selection(actor=request.user,candidate=candidate,**serializer.validated_data)
        return Response(PortfolioSelectionSerializer(item).data)
