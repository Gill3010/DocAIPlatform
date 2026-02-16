/**
 * API unificada: reúne todos los módulos en un solo objeto para compatibilidad con imports existentes.
 */
import * as auth from './auth';
import * as users from './users';
import * as convert from './convert';
import * as admin from './admin';
import * as ai from './ai';
import * as pdfTools from './pdfTools';
import * as documents from './documents';

export const apiService = {
    login: auth.login,
    getGoogleAuthUrl: auth.getGoogleAuthUrl,
    googleAuth: auth.googleAuth,
    getFacebookAuthUrl: auth.getFacebookAuthUrl,
    facebookAuth: auth.facebookAuth,
    register: auth.register,
    linkAnonymousSession: auth.linkAnonymousSession,
    getCurrentUser: users.getCurrentUser,
    getProfile: users.getProfile,
    updateProfile: users.updateProfile,
    uploadAvatar: users.uploadAvatar,
    getUserStats: users.getUserStats,
    getAnonymousStats: users.getAnonymousStats,
    searchUsers: users.searchUsers,
    uploadAndConvert: convert.uploadAndConvert,
    downloadConvertedFile: convert.downloadConvertedFile,
    getConversionHistory: convert.getConversionHistory,
    getConversionStatus: convert.getConversionStatus,
    getSupportedFormats: convert.getSupportedFormats,
    getAdminMe: admin.getAdminMe,
    getAdminStats: admin.getAdminStats,
    getAdminUsers: admin.getAdminUsers,
    getAdminUser: admin.getAdminUser,
    patchAdminUser: admin.patchAdminUser,
    getAdminConversions: admin.getAdminConversions,
    getAdminPayments: admin.getAdminPayments,
    getAdminActivity: admin.getAdminActivity,
    sendChatMessage: ai.sendChatMessage,
    getAICredits: ai.getAICredits,
    pdfTool: pdfTools.pdfTool,
    createDocumentFromConversion: documents.createDocumentFromConversion,
    getDocuments: documents.getDocuments,
    getDocument: documents.getDocument,
    deleteDocument: documents.deleteDocument,
    getDocumentPermissions: documents.getDocumentPermissions,
    addDocumentPermission: documents.addDocumentPermission,
    removeDocumentPermission: documents.removeDocumentPermission,
};

export { getAvatarUrl } from './config';
export { ApiError, apiErrorFromResponse } from './errors';
