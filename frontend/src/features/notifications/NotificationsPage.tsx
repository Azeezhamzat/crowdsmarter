import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router";

import { StatusMessage } from "../../components/StatusMessage";
import { listNotifications, markAllNotificationsRead, markNotificationRead } from "./api";

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function NotificationsPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const inbox = useQuery({
    queryKey: ["notifications"],
    queryFn: () => listNotifications(false),
  });
  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ["notifications"] });
  };
  const markOne = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: refresh,
  });
  const markAll = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: refresh,
  });

  const openNotification = async (id: string, url: string) => {
    await markOne.mutateAsync(id);
    if (url) await navigate(url);
  };

  return (
    <div>
      <Link className="back-link" to="/app">← Organisations</Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Your work</p>
          <h1>Notifications</h1>
          <p className="muted">Assignments, lifecycle changes, due reviews, and completed advisory reviews.</p>
        </div>
        {inbox.data?.unread_count ? (
          <button className="button button--secondary" type="button" disabled={markAll.isPending} onClick={() => markAll.mutate()}>
            {markAll.isPending ? "Marking…" : "Mark all as read"}
          </button>
        ) : null}
      </div>

      {inbox.isPending ? <p>Loading notifications…</p> : null}
      {inbox.isError ? <StatusMessage kind="error">Notifications could not be loaded.</StatusMessage> : null}
      {inbox.data?.notifications.length === 0 ? (
        <div className="empty-state"><h2>No notifications</h2><p>New assignments and workflow updates will appear here.</p></div>
      ) : null}
      <div className="notification-list">
        {inbox.data?.notifications.map((notification) => (
          <article className={`notification-card${notification.is_read ? " notification-card--read" : ""}`} key={notification.id}>
            <div>
              <div className="notification-card__meta">
                <span className="role-badge">{notification.kind_label}</span>
                <time dateTime={notification.created_at}>{formatDate(notification.created_at)}</time>
              </div>
              <h2>{notification.title}</h2>
              <p>{notification.message}</p>
            </div>
            <div className="inline-actions">
              {notification.url ? (
                <button className="button button--primary" type="button" onClick={() => void openNotification(notification.id, notification.url)}>
                  Open
                </button>
              ) : null}
              {!notification.is_read ? (
                <button className="button button--quiet" type="button" disabled={markOne.isPending} onClick={() => markOne.mutate(notification.id)}>
                  Mark read
                </button>
              ) : null}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
