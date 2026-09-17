
"use strict";

// ============================================================
// ADMIN CONFIG
// ============================================================

const ADMIN_IDS = new Set(
  String(process.env.ADMIN_IDS || "")
    .split(",")
    .map((id) => id.trim())
    .filter(Boolean)
);

// ============================================================
// PERMISSION CHECKS
// ============================================================

function isAdmin(userID) {
  if (!userID) {
    return false;
  }

  return ADMIN_IDS.has(
    String(userID)
  );
}

function canAnnounce(userID) {
  return isAdmin(userID);
}

function canModerate(userID) {
  return isAdmin(userID);
}

function canManageBot(userID) {
  return isAdmin(userID);
}

function canManageEconomy(userID) {
  return isAdmin(userID);
}

// ============================================================
// ADMIN LIST
// ============================================================

function getAdminIDs() {
  return [
    ...ADMIN_IDS,
  ];
}

// ============================================================
// EXPORTS
// ============================================================

module.exports = {
  isAdmin,
  canAnnounce,
  canModerate,
  canManageBot,
  canManageEconomy,
  getAdminIDs,
};
