import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { getTerminology } from "../../lib/terminology";
import type { ConflictOfInterest, ConflictOfInterestScope, DecisionOption, Participant, ParticipantRole } from "../../lib/types";
import { fetchCurrentUser } from "../auth/api";
import { listOptions } from "../reasoning/api";
import {
  addParticipant,
  changeParticipantRole,
  declareConflict,
  listConflicts,
  listParticipants,
  removeParticipant,
  withdrawConflict,
} from "./api";

function ConflictControl({
  decisionId,
  participant,
  conflicts,
  canDeclare,
  canManage,
}: {
  decisionId: string;
  participant: Participant;
  conflicts: ConflictOfInterest[];
  canDeclare: boolean;
  canManage: boolean;
}) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [scope, setScope] = useState<ConflictOfInterestScope>("option");
  const [optionId, setOptionId] = useState("");
  const [reason, setReason] = useState("");

  const options = useQuery({
    queryKey: ["decisions", decisionId, "options"],
    queryFn: () => listOptions(decisionId),
    enabled: open,
  });

  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: ["decisions", decisionId, "conflicts"] });

  const declare = useMutation({
    mutationFn: () =>
      declareConflict(participant.id, {
        scope,
        option_id: scope === "option" ? optionId || null : null,
        reason,
      }),
    onSuccess: async () => {
      setOpen(false);
      setReason("");
      setOptionId("");
      await refresh();
    },
  });
  const withdraw = useMutation({
    mutationFn: (conflictId: string) => withdrawConflict(conflictId),
    onSuccess: refresh,
  });

  const ownConflicts = conflicts.filter((item) => item.participant_id === participant.id);

  return (
    <div className="participant-conflicts">
      {ownConflicts.map((conflict) => (
        <div key={conflict.id} className="inline-badges">
          <span className="role-badge">
            Conflict: {conflict.scope === "option" ? conflict.option_title ?? "an option" : "entire round"}
          </span>
          {canManage || canDeclare ? (
            <button
              className="button button--quiet button--compact"
              type="button"
              disabled={withdraw.isPending}
              onClick={() => withdraw.mutate(conflict.id)}
            >
              Withdraw
            </button>
          ) : null}
        </div>
      ))}
      {(canDeclare || canManage) && !open ? (
        <button className="button button--quiet button--compact" type="button" onClick={() => setOpen(true)}>
          Declare a conflict
        </button>
      ) : null}
      {open ? (
        <div className="participant-conflict-form">
          <select value={scope} onChange={(event) => setScope(event.target.value as ConflictOfInterestScope)}>
            <option value="option">On one application</option>
            <option value="decision">On the entire round</option>
          </select>
          {scope === "option" ? (
            <select value={optionId} onChange={(event) => setOptionId(event.target.value)}>
              <option value="">Select an application…</option>
              {(options.data ?? []).map((item: DecisionOption) => (
                <option key={item.id} value={item.id}>{item.title}</option>
              ))}
            </select>
          ) : null}
          <input placeholder="Reason (optional)" value={reason} onChange={(event) => setReason(event.target.value)} />
          <div className="button-row">
            <button
              className="button button--primary button--compact"
              type="button"
              disabled={declare.isPending || (scope === "option" && !optionId)}
              onClick={() => declare.mutate()}
            >
              {declare.isPending ? "Saving…" : "Save"}
            </button>
            <button className="button button--quiet button--compact" type="button" onClick={() => setOpen(false)}>
              Cancel
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

const assignableRoles = ["decision_maker", "contributor", "reviewer", "observer"] as const;

const participantSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  role: z.enum(assignableRoles),
});

type ParticipantInput = z.infer<typeof participantSchema>;

type AssignableRole = Exclude<ParticipantRole, "decision_owner">;

export function ParticipantsPanel({
  decisionId,
  canManage,
  templateKey,
}: {
  decisionId: string;
  canManage: boolean;
  templateKey?: string | null;
}) {
  const terms = getTerminology(templateKey);
  const roleLabel = (role: string) => terms.roleLabels[role as ParticipantRole] ?? role.replaceAll("_", " ");
  const queryClient = useQueryClient();
  const participants = useQuery({
    queryKey: ["decisions", decisionId, "participants"],
    queryFn: () => listParticipants(decisionId),
  });
  const currentUser = useQuery({ queryKey: ["current-user"], queryFn: fetchCurrentUser });
  const myParticipant = participants.data?.find((item) => item.user.id === currentUser.data?.id);
  const conflicts = useQuery({
    queryKey: ["decisions", decisionId, "conflicts"],
    queryFn: () => listConflicts(myParticipant!.id),
    enabled: Boolean(myParticipant),
  });
  const form = useForm<ParticipantInput>({
    resolver: zodResolver(participantSchema),
    defaultValues: { email: "", role: "contributor" },
  });

  const refresh = async () => {
    await queryClient.invalidateQueries({
      queryKey: ["decisions", decisionId, "participants"],
    });
    await queryClient.invalidateQueries({ queryKey: ["decisions", decisionId] });
  };

  const add = useMutation({
    mutationFn: (input: ParticipantInput) => addParticipant(decisionId, input),
    onSuccess: async () => {
      form.reset({ email: "", role: "contributor" });
      await refresh();
    },
  });
  const changeRole = useMutation({
    mutationFn: ({ participantId, role }: { participantId: string; role: AssignableRole }) =>
      changeParticipantRole(participantId, role),
    onSuccess: refresh,
  });
  const remove = useMutation({
    mutationFn: removeParticipant,
    onSuccess: refresh,
  });

  const mutationError = add.error ?? changeRole.error ?? remove.error;

  return (
    <section className="side-panel participants-panel" aria-labelledby="participants-title">
      <h2 id="participants-title">{terms.committeeLabel}</h2>
      <p className="muted">Make stakeholder involvement explicit before contribution opens.</p>
      {participants.isPending ? <p>Loading {terms.committeeLabel.toLowerCase()}…</p> : null}
      {participants.isError ? (
        <StatusMessage kind="error">{terms.committeeLabel} could not be loaded.</StatusMessage>
      ) : null}
      {mutationError ? (
        <StatusMessage kind="error">
          {mutationError instanceof ApiError
            ? mutationError.message
            : `The ${terms.committeeLabel.toLowerCase()} change failed.`}
        </StatusMessage>
      ) : null}

      <div className="participant-list">
        {participants.data?.map((participant) => (
          <div className="participant-row" key={participant.id}>
            <div>
              <strong>
                {participant.user.first_name || participant.user.last_name
                  ? `${participant.user.first_name} ${participant.user.last_name}`.trim()
                  : participant.user.email}
              </strong>
              <span className="table-secondary">{participant.user.email}</span>
            </div>
            {participant.role === "decision_owner" || !canManage ? (
              <span className="role-badge">{terms.roleLabels[participant.role] ?? participant.role_label}</span>
            ) : (
              <div className="participant-actions">
                <select
                  aria-label={`Role for ${participant.user.email}`}
                  value={participant.role}
                  disabled={changeRole.isPending}
                  onChange={(event) =>
                    changeRole.mutate({
                      participantId: participant.id,
                      role: event.target.value as AssignableRole,
                    })
                  }
                >
                  {assignableRoles.map((role) => (
                    <option value={role} key={role}>
                      {roleLabel(role)}
                    </option>
                  ))}
                </select>
                <button
                  className="button button--danger-quiet"
                  type="button"
                  disabled={remove.isPending}
                  onClick={() => {
                    if (window.confirm(`Remove ${participant.user.email} from this decision?`)) {
                      remove.mutate(participant.id);
                    }
                  }}
                >
                  Remove
                </button>
              </div>
            )}
            {participant.role === "decision_owner" ? null : (
              <ConflictControl
                decisionId={decisionId}
                participant={participant}
                conflicts={conflicts.data ?? []}
                canDeclare={participant.user.id === currentUser.data?.id}
                canManage={canManage}
              />
            )}
          </div>
        ))}
      </div>

      {canManage ? (
        <form className="participant-form" onSubmit={form.handleSubmit((values) => add.mutate(values))} noValidate>
          <h3>Add a stakeholder</h3>
          <label htmlFor="participant-email">Organisation member email</label>
          <input id="participant-email" type="email" {...form.register("email")} />
          <FieldError message={form.formState.errors.email?.message} />

          <label htmlFor="participant-role">{terms.decisionNoun} role</label>
          <select id="participant-role" {...form.register("role")}>
            {assignableRoles.map((role) => (
              <option value={role} key={role}>
                {roleLabel(role)}
              </option>
            ))}
          </select>

          <button className="button button--primary button--full" type="submit" disabled={add.isPending}>
            {add.isPending ? "Adding…" : "Add participant"}
          </button>
        </form>
      ) : null}
    </section>
  );
}
