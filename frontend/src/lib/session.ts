export const LOCAL_USER_ID_KEY = "fff_user_id";
export const LOCAL_USER_NAME_KEY = "fff_user_name";

export function getLocalUserId(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(LOCAL_USER_ID_KEY);
}

export function setLocalUser(userId: string, name: string) {
  window.localStorage.setItem(LOCAL_USER_ID_KEY, userId);
  window.localStorage.setItem(LOCAL_USER_NAME_KEY, name);
}

export function clearLocalUser() {
  window.localStorage.removeItem(LOCAL_USER_ID_KEY);
  window.localStorage.removeItem(LOCAL_USER_NAME_KEY);
}

export function getLocalUserName(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(LOCAL_USER_NAME_KEY);
}

