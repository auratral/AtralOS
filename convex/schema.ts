import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  patients: defineTable({
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
  }).index("by_custom_id", ["id"]),

  appointments: defineTable({
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
  }).index("by_custom_id", ["id"]).index("by_patientId", ["patientId"]).index("by_department", ["department"]),

  clinicalRecords: defineTable({
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
  }).index("by_custom_id", ["id"]).index("by_patientId", ["patientId"]),

  investigations: defineTable({
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
  }).index("by_custom_id", ["id"]).index("by_patientId", ["patientId"]),

  billingInvoices: defineTable({
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
  }).index("by_custom_id", ["id"]).index("by_patientId", ["patientId"]),

  auditLogs: defineTable({
    id: v.string(),
    timestamp: v.string(),
    userRole: v.string(),
    userId: v.string(),
    userName: v.string(),
    actionType: v.string(),
    recordId: v.string(),
    description: v.string(),
    device: v.string(),
  }).index("by_custom_id", ["id"]),

  staffAccounts: defineTable({
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
  }).index("by_custom_id", ["id"]),

  vitals: defineTable({
    id: v.string(),
    patientId: v.string(),
    bp: v.string(),
    temp: v.number(),
    spo2: v.number(),
    pulse: v.number(),
    sugar: v.number(),
    notes: v.string(),
    timestamp: v.string(),
  }).index("by_custom_id", ["id"]).index("by_patientId", ["patientId"]),

  devices: defineTable({
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
  }).index("by_custom_id", ["id"]).index("by_department", ["department"]),

  complaints: defineTable({
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
  }).index("by_custom_id", ["id"]).index("by_department", ["department"]),

  notifications: defineTable({
    id: v.string(),
    userId: v.string(),
    title: v.string(),
    message: v.string(),
    type: v.string(),
    read: v.boolean(),
    timestamp: v.string(),
  }).index("by_custom_id", ["id"]).index("by_userId", ["userId"]),
});
