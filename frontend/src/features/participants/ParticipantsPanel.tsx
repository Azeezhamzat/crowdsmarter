import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type { ParticipantRole } from "../../lib/types";
import {
  addParticipant,
  changeParticipantRole,
  listParticipants,
  removeParticipant,
} from "./api";

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
}: {
  decisionId: string;
  canManage: boolean;
}) {
  const queryClient = useQueryClient();
  const participants = useQuery({
    queryKey: ["decisions", decisionId, "participants"],
    queryFn: () => listParticipants(decisionId),
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
      <h2 id="participants-title">Participants</h2>
      <p className="muted">Make stakeholder involvement explicit before contribution opens.</p>
      {participants.isPending ? <p>Loading participants…</p> : null}
      {participants.isError ? (
        <StatusMessage kind="error">Participants could not be loaded.</StatusMessage>
      ) : null}
      {mutationError ? (
        <StatusMessage kind="error">
          {mutationError instanceof ApiError
            ? mutationError.message
            : "The participant change failed."}
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
              <span className="role-badge">{participant.role_label}</span>
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
                      {role.replaceAll("_", " ")}
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
          </div>
        ))}
      </div>

      {canManage ? (
        <form className="participant-form" onSubmit={form.handleSubmit((values) => add.mutate(values))} noValidate>
          <h3>Add a stakeholder</h3>
          <label htmlFor="participant-email">Organisation member email</label>
          <input id="participant-email" type="email" {...form.register("email")} />
          <FieldError message={form.formState.errors.email?.message} />

          <label htmlFor="participant-role">Decision role</label>
          <select id="participant-role" {...form.register("role")}>
            {assignableRoles.map((role) => (
              <option value={role} key={role}>
                {role.replaceAll("_", " ")}
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
