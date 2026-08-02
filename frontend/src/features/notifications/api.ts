import { apiRequest } from "../../lib/api";
import type { Notification, NotificationInbox } from "../../lib/types";

export function listNotifications(unreadOnly = false): Promise<NotificationInbox> {
  const suffix = unreadOnly ? "?unread=true" : "";
  return apiRequest<NotificationInbox>(`/notifications/${suffix}`);
}

export function markNotificationRead(notificationId: string): Promise<Notification> {
  return apiRequest<Notification>(`/notifications/${notificationId}/read/`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function markAllNotificationsRead(): Promise<{ marked_read: number }> {
  return apiRequest<{ marked_read: number }>("/notifications/read-all/", {
    method: "POST",
    body: JSON.stringify({}),
  });
}
