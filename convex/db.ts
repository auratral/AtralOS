import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

// ==========================================
// 1. QUERY HANDLERS
// ==========================================

export const getPatients = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("patients").collect();
  },
});

export const getAppointments = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("appointments").collect();
  },
});

export const getClinicalRecords = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("clinicalRecords").collect();
  },
});

export const getInvestigations = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("investigations").collect();
  },
});

export const getBillingInvoices = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("billingInvoices").collect();
  },
});

export const getAuditLogs = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("auditLogs").collect();
  },
});

export const getStaffAccounts = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("staffAccounts").collect();
  },
});

export const getVitals = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("vitals").collect();
  },
});

export const getDevices = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("devices").collect();
  },
});

export const getComplaints = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("complaints").collect();
  },
});

export const getNotifications = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("notifications").collect();
  },
});

// ==========================================
// 2. MUTATION HANDLERS (UPSERTS & SEED)
// ==========================================

export const upsertPatient = mutation({
  args: {
    id: v.string(),
    name: v.string(),
    dob: v.string(),
    gender: v.string(),
    mobile: v.string(),
    bloodGroup: v.string(),
    emergency: v.string(),
    insurance: v.string(),
    abhaId: v.string(),
    consentAcademic: v.boolean(),
    consentCommercial: v.boolean(),
    consentFuture: v.boolean(),
    regDate: v.string(),
    status: v.string(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("patients")
      .withIndex("by_custom_id", (q) => q.eq("id", args.id))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, args);
    } else {
      await ctx.db.insert("patients", args);
    }
  },
});

export const upsertVitals = mutation({
  args: {
    id: v.string(),
    patientId: v.string(),
    bp: v.string(),
    temp: v.number(),
    spo2: v.number(),
    pulse: v.number(),
    sugar: v.number(),
    notes: v.string(),
    timestamp: v.string(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("vitals")
      .withIndex("by_custom_id", (q) => q.eq("id", args.id))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, args);
    } else {
      await ctx.db.insert("vitals", args);
    }
  },
});

export const upsertAppointment = mutation({
  args: {
    id: v.string(),
    patientId: v.string(),
    doctorId: v.string(),
    department: v.string(),
    type: v.string(),
    date: v.string(),
    time: v.string(),
    status: v.string(),
    token: v.number(),
    investigationStatus: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("appointments")
      .withIndex("by_custom_id", (q) => q.eq("id", args.id))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, {
        id: args.id,
        patientId: args.patientId,
        doctorId: args.doctorId,
        department: args.department,
        type: args.type,
        date: args.date,
        time: args.time,
        status: args.status,
        token: args.token,
        investigationStatus: args.investigationStatus,
      });
    } else {
      await ctx.db.insert("appointments", {
        id: args.id,
        patientId: args.patientId,
        doctorId: args.doctorId,
        department: args.department,
        type: args.type,
        date: args.date,
        time: args.time,
        status: args.status,
        token: args.token,
        investigationStatus: args.investigationStatus,
      });
    }
  },
});

export const upsertClinicalRecord = mutation({
  args: {
    id: v.string(),
    patientId: v.string(),
    doctorId: v.string(),
    doctorName: v.string(),
    date: v.string(),
    s: v.string(),
    o: v.string(),
    a: v.array(v.string()),
    p: v.string(),
    medicines: v.array(
      v.object({
        name: v.string(),
        dose: v.string(),
        freq: v.string(),
        duration: v.string(),
      })
    ),
    signed: v.boolean(),
    signee: v.string(),
    consentFlag: v.boolean(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("clinicalRecords")
      .withIndex("by_custom_id", (q) => q.eq("id", args.id))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, args);
    } else {
      await ctx.db.insert("clinicalRecords", args);
    }
  },
});

export const upsertInvestigation = mutation({
  args: {
    id: v.string(),
    patientId: v.string(),
    doctorId: v.string(),
    doctorName: v.string(),
    type: v.string(),
    testName: v.string(),
    refRange: v.optional(v.string()),
    value: v.optional(v.string()),
    urgency: v.optional(v.string()),
    status: v.string(),
    date: v.string(),
    image: v.optional(v.string()),
    comments: v.optional(v.string()),
    returnToDoctor: v.optional(v.boolean()),
    medicines: v.optional(
      v.array(
        v.object({
          name: v.string(),
          dose: v.string(),
          freq: v.string(),
          duration: v.string(),
        })
      )
    ),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("investigations")
      .withIndex("by_custom_id", (q) => q.eq("id", args.id))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, {
        id: args.id,
        patientId: args.patientId,
        doctorId: args.doctorId,
        doctorName: args.doctorName,
        type: args.type,
        testName: args.testName,
        refRange: args.refRange,
        value: args.value,
        urgency: args.urgency,
        status: args.status,
        date: args.date,
        image: args.image,
        comments: args.comments,
        returnToDoctor: args.returnToDoctor,
        medicines: args.medicines,
      });
    } else {
      await ctx.db.insert("investigations", {
        id: args.id,
        patientId: args.patientId,
        doctorId: args.doctorId,
        doctorName: args.doctorName,
        type: args.type,
        testName: args.testName,
        refRange: args.refRange,
        value: args.value,
        urgency: args.urgency,
        status: args.status,
        date: args.date,
        image: args.image,
        comments: args.comments,
        returnToDoctor: args.returnToDoctor,
        medicines: args.medicines,
      });
    }
  },
});

export const upsertBillingInvoice = mutation({
  args: {
    id: v.string(),
    patientId: v.string(),
    date: v.string(),
    items: v.array(
      v.object({
        serviceName: v.string(),
        qty: v.number(),
        rate: v.number(),
        amount: v.number(),
      })
    ),
    subtotal: v.number(),
    gst: v.number(),
    insuranceClaim: v.number(),
    tpaApproved: v.boolean(),
    preAuthApproved: v.boolean(),
    preAuthNum: v.optional(v.string()),
    paymentMode: v.optional(v.string()),
    total: v.number(),
    status: v.string(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("billingInvoices")
      .withIndex("by_custom_id", (q) => q.eq("id", args.id))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, args);
    } else {
      await ctx.db.insert("billingInvoices", args);
    }
  },
});

export const upsertAuditLog = mutation({
  args: {
    id: v.string(),
    timestamp: v.string(),
    userRole: v.string(),
    userId: v.string(),
    userName: v.string(),
    actionType: v.string(),
    recordId: v.string(),
    description: v.string(),
    device: v.string(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("auditLogs")
      .withIndex("by_custom_id", (q) => q.eq("id", args.id))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, args);
    } else {
      await ctx.db.insert("auditLogs", args);
    }
  },
});

export const upsertStaffAccount = mutation({
  args: {
    id: v.string(),
    name: v.string(),
    role: v.string(),
    dept: v.string(),
    license: v.string(),
    status: v.string(),
    shift: v.optional(v.string()),
    workDays: v.optional(v.string()),
    qualification: v.optional(v.string()),
    specialization: v.optional(v.string()),
    phone: v.optional(v.string()),
    email: v.optional(v.string()),
    leaveBalance: v.optional(v.number()),
    joiningDate: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("staffAccounts")
      .withIndex("by_custom_id", (q) => q.eq("id", args.id))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, {
        id: args.id,
        name: args.name,
        role: args.role,
        dept: args.dept,
        license: args.license,
        status: args.status,
        shift: args.shift,
        workDays: args.workDays,
        qualification: args.qualification,
        specialization: args.specialization,
        phone: args.phone,
        email: args.email,
        leaveBalance: args.leaveBalance,
        joiningDate: args.joiningDate,
      });
    } else {
      await ctx.db.insert("staffAccounts", {
        id: args.id,
        name: args.name,
        role: args.role,
        dept: args.dept,
        license: args.license,
        status: args.status,
        shift: args.shift,
        workDays: args.workDays,
        qualification: args.qualification,
        specialization: args.specialization,
        phone: args.phone,
        email: args.email,
        leaveBalance: args.leaveBalance,
        joiningDate: args.joiningDate,
      });
    }
  },
});

export const upsertDevice = mutation({
  args: {
    id: v.string(),
    name: v.string(),
    type: v.string(),
    department: v.string(),
    location: v.string(),
    status: v.string(),
    serialNumber: v.string(),
    purchaseDate: v.string(),
    maintenanceDue: v.string(),
    lastMaintenance: v.string(),
    warranty: v.string(),
    notes: v.string(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("devices")
      .withIndex("by_custom_id", (q) => q.eq("id", args.id))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, args);
    } else {
      await ctx.db.insert("devices", args);
    }
  },
});

export const upsertComplaint = mutation({
  args: {
    id: v.string(),
    title: v.string(),
    category: v.string(),
    department: v.string(),
    priority: v.string(),
    status: v.string(),
    reportedBy: v.string(),
    assignedTo: v.string(),
    description: v.string(),
    resolution: v.string(),
    createdAt: v.string(),
    resolvedAt: v.string(),
    comments: v.optional(v.array(v.object({
      author: v.string(),
      text: v.string(),
      timestamp: v.string(),
    }))),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("complaints")
      .withIndex("by_custom_id", (q) => q.eq("id", args.id))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, {
        id: args.id,
        title: args.title,
        category: args.category,
        department: args.department,
        priority: args.priority,
        status: args.status,
        reportedBy: args.reportedBy,
        assignedTo: args.assignedTo,
        description: args.description,
        resolution: args.resolution,
        createdAt: args.createdAt,
        resolvedAt: args.resolvedAt,
        comments: args.comments,
      });
    } else {
      await ctx.db.insert("complaints", {
        id: args.id,
        title: args.title,
        category: args.category,
        department: args.department,
        priority: args.priority,
        status: args.status,
        reportedBy: args.reportedBy,
        assignedTo: args.assignedTo,
        description: args.description,
        resolution: args.resolution,
        createdAt: args.createdAt,
        resolvedAt: args.resolvedAt,
        comments: args.comments,
      });
    }
  },
});

export const upsertNotification = mutation({
  args: {
    id: v.string(),
    userId: v.string(),
    title: v.string(),
    message: v.string(),
    type: v.string(),
    read: v.boolean(),
    timestamp: v.string(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("notifications")
      .withIndex("by_custom_id", (q) => q.eq("id", args.id))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, args);
    } else {
      await ctx.db.insert("notifications", args);
    }
  },
});

export const seedDatabases = mutation({
  args: {
    patients: v.array(v.any()),
    appointments: v.array(v.any()),
    clinicalRecords: v.array(v.any()),
    investigations: v.array(v.any()),
    billingInvoices: v.array(v.any()),
    staffAccounts: v.array(v.any()),
    auditLogs: v.array(v.any()),
    vitals: v.array(v.any()),
    devices: v.optional(v.array(v.any())),
    complaints: v.optional(v.array(v.any())),
    notifications: v.optional(v.array(v.any())),
  },
  handler: async (ctx, args) => {
    // Clear all existing data first
    const ps = await ctx.db.query("patients").collect();
    for (const p of ps) await ctx.db.delete(p._id);
    const apts = await ctx.db.query("appointments").collect();
    for (const a of apts) await ctx.db.delete(a._id);
    const crs = await ctx.db.query("clinicalRecords").collect();
    for (const c of crs) await ctx.db.delete(c._id);
    const invs = await ctx.db.query("investigations").collect();
    for (const i of invs) await ctx.db.delete(i._id);
    const bills = await ctx.db.query("billingInvoices").collect();
    for (const b of bills) await ctx.db.delete(b._id);
    const staff = await ctx.db.query("staffAccounts").collect();
    for (const s of staff) await ctx.db.delete(s._id);
    const audits = await ctx.db.query("auditLogs").collect();
    for (const a of audits) await ctx.db.delete(a._id);
    const vits = await ctx.db.query("vitals").collect();
    for (const vt of vits) await ctx.db.delete(vt._id);
    const devs = await ctx.db.query("devices").collect();
    for (const d of devs) await ctx.db.delete(d._id);
    const comps = await ctx.db.query("complaints").collect();
    for (const c of comps) await ctx.db.delete(c._id);
    const notifs = await ctx.db.query("notifications").collect();
    for (const n of notifs) await ctx.db.delete(n._id);

    // Seed clean, decoupled tables
    for (const item of args.patients) await ctx.db.insert("patients", item);
    for (const item of args.appointments) await ctx.db.insert("appointments", item);
    for (const item of args.clinicalRecords) await ctx.db.insert("clinicalRecords", item);
    for (const item of args.investigations) await ctx.db.insert("investigations", item);
    for (const item of args.billingInvoices) await ctx.db.insert("billingInvoices", item);
    for (const item of args.staffAccounts) await ctx.db.insert("staffAccounts", item);
    for (const item of args.auditLogs) await ctx.db.insert("auditLogs", item);
    for (const item of args.vitals) await ctx.db.insert("vitals", item);
    if (args.devices) for (const item of args.devices) await ctx.db.insert("devices", item);
    if (args.complaints) for (const item of args.complaints) await ctx.db.insert("complaints", item);
    if (args.notifications) for (const item of args.notifications) await ctx.db.insert("notifications", item);
  },
});
