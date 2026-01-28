'use client';

import { useState, useEffect } from 'react';
import {
    Search,
    Edit2,
    Trash2,
    X,
    Check,
    AlertTriangle,
    User,
    Shield,
    Ban,
} from 'lucide-react';
import { apiClient } from '@/lib/api/client';

interface User {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    user_type: 'borrower' | 'loan_officer' | 'realtor' | 'admin';
    is_active: boolean;
    is_verified: boolean;
    created_at: string;
}

const USER_TYPES = [
    { value: 'borrower', label: 'Borrower' },
    { value: 'loan_officer', label: 'Loan Officer' },
    { value: 'realtor', label: 'Realtor' },
    { value: 'admin', label: 'Admin' },
];

export default function AdminUsersPage() {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [editUser, setEditUser] = useState<User | null>(null);
    const [deleteUser, setDeleteUser] = useState<User | null>(null);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [editForm, setEditForm] = useState({
        first_name: '',
        last_name: '',
        email: '',
        user_type: 'borrower' as User['user_type'],
        is_active: true,
    });

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        try {
            const { data } = await apiClient.get('/admin/users');
            setUsers(data.users || []);
        } catch {
            setError('Failed to load users');
        } finally {
            setLoading(false);
        }
    };

    const filteredUsers = users.filter(user =>
        user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        `${user.first_name} ${user.last_name}`.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const openEditModal = (user: User) => {
        setEditUser(user);
        setEditForm({
            first_name: user.first_name,
            last_name: user.last_name,
            email: user.email,
            user_type: user.user_type,
            is_active: user.is_active,
        });
        setError(null);
    };

    const handleSaveEdit = async () => {
        if (!editUser) return;
        setSaving(true);
        setError(null);

        try {
            await apiClient.patch(`/admin/users/${editUser.id}`, editForm);
            setUsers(prev => prev.map(u =>
                u.id === editUser.id ? { ...u, ...editForm } : u
            ));
            setEditUser(null);
        } catch {
            setError('Failed to update user');
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async () => {
        if (!deleteUser) return;
        setSaving(true);

        try {
            await apiClient.delete(`/admin/users/${deleteUser.id}`);
            setUsers(prev => prev.filter(u => u.id !== deleteUser.id));
            setDeleteUser(null);
        } catch {
            setError('Failed to delete user');
        } finally {
            setSaving(false);
        }
    };

    const toggleUserStatus = async (user: User) => {
        try {
            await apiClient.patch(`/admin/users/${user.id}/status`, {
                is_active: !user.is_active
            });
            setUsers(prev => prev.map(u =>
                u.id === user.id ? { ...u, is_active: !u.is_active } : u
            ));
        } catch {
            setError('Failed to update status');
        }
    };

    if (loading) {
        return (
            <div className="p-6 max-w-6xl mx-auto">
                <div className="animate-pulse space-y-4">
                    <div className="h-8 bg-gray-200 rounded w-1/4" />
                    <div className="h-12 bg-gray-200 rounded" />
                    <div className="space-y-2">
                        {[1, 2, 3, 4, 5].map(i => (
                            <div key={i} className="h-16 bg-gray-200 rounded" />
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 max-w-6xl mx-auto">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
                <p className="text-gray-600">Manage platform users and permissions</p>
            </div>

            {/* Search */}
            <div className="mb-6">
                <div className="relative max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search users..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                </div>
            </div>

            {/* Error */}
            {error && (
                <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
                    <AlertTriangle className="w-5 h-5" />
                    {error}
                    <button onClick={() => setError(null)} className="ml-auto">
                        <X className="w-4 h-4" />
                    </button>
                </div>
            )}

            {/* Users Table */}
            <div className="bg-white rounded-xl border overflow-hidden">
                <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Joined</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y">
                        {filteredUsers.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                                    No users found
                                </td>
                            </tr>
                        ) : (
                            filteredUsers.map(user => (
                                <tr key={user.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                                                <User className="w-5 h-5 text-gray-500" />
                                            </div>
                                            <div>
                                                <p className="font-medium text-gray-900">
                                                    {user.first_name} {user.last_name}
                                                </p>
                                                <p className="text-sm text-gray-500">{user.email}</p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${user.user_type === 'admin'
                                                ? 'bg-purple-100 text-purple-800'
                                                : user.user_type === 'loan_officer'
                                                    ? 'bg-blue-100 text-blue-800'
                                                    : 'bg-gray-100 text-gray-800'
                                            }`}>
                                            {user.user_type === 'admin' && <Shield className="w-3 h-3" />}
                                            {USER_TYPES.find(t => t.value === user.user_type)?.label}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <button
                                            onClick={() => toggleUserStatus(user)}
                                            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${user.is_active
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-red-100 text-red-800'
                                                }`}
                                        >
                                            {user.is_active ? (
                                                <><Check className="w-3 h-3" /> Active</>
                                            ) : (
                                                <><Ban className="w-3 h-3" /> Inactive</>
                                            )}
                                        </button>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-500">
                                        {new Date(user.created_at).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center justify-end gap-2">
                                            <button
                                                onClick={() => openEditModal(user)}
                                                className="p-2 hover:bg-gray-100 rounded-lg text-gray-600"
                                                title="Edit user"
                                            >
                                                <Edit2 className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => setDeleteUser(user)}
                                                className="p-2 hover:bg-red-100 rounded-lg text-red-600"
                                                title="Delete user"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Edit Modal */}
            {editUser && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-semibold">Edit User</h2>
                            <button onClick={() => setEditUser(null)} className="p-2 hover:bg-gray-100 rounded-lg">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        First Name
                                    </label>
                                    <input
                                        type="text"
                                        value={editForm.first_name}
                                        onChange={(e) => setEditForm(f => ({ ...f, first_name: e.target.value }))}
                                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Last Name
                                    </label>
                                    <input
                                        type="text"
                                        value={editForm.last_name}
                                        onChange={(e) => setEditForm(f => ({ ...f, last_name: e.target.value }))}
                                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Email
                                </label>
                                <input
                                    type="email"
                                    value={editForm.email}
                                    onChange={(e) => setEditForm(f => ({ ...f, email: e.target.value }))}
                                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    User Type
                                </label>
                                <select
                                    value={editForm.user_type}
                                    onChange={(e) => setEditForm(f => ({ ...f, user_type: e.target.value as User['user_type'] }))}
                                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                >
                                    {USER_TYPES.map(type => (
                                        <option key={type.value} value={type.value}>{type.label}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="flex items-center gap-3">
                                <button
                                    onClick={() => setEditForm(f => ({ ...f, is_active: !f.is_active }))}
                                    role="switch"
                                    aria-checked={editForm.is_active}
                                    className={`relative w-12 h-6 rounded-full transition-colors ${editForm.is_active ? 'bg-blue-600' : 'bg-gray-200'
                                        }`}
                                >
                                    <span className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${editForm.is_active ? 'translate-x-7' : 'translate-x-1'
                                        }`} />
                                </button>
                                <span className="text-sm text-gray-700">Active</span>
                            </div>
                        </div>

                        <div className="flex gap-3 mt-6">
                            <button
                                onClick={() => setEditUser(null)}
                                className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSaveEdit}
                                disabled={saving}
                                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                            >
                                {saving ? 'Saving...' : 'Save Changes'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {deleteUser && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-xl p-6 w-full max-w-sm mx-4">
                        <div className="text-center">
                            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Trash2 className="w-6 h-6 text-red-600" />
                            </div>
                            <h2 className="text-xl font-semibold text-gray-900 mb-2">Delete User?</h2>
                            <p className="text-gray-500 mb-6">
                                Are you sure you want to delete <strong>{deleteUser.first_name} {deleteUser.last_name}</strong>?
                                This action cannot be undone.
                            </p>
                            <div className="flex gap-3">
                                <button
                                    onClick={() => setDeleteUser(null)}
                                    className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleDelete}
                                    disabled={saving}
                                    className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                                >
                                    {saving ? 'Deleting...' : 'Delete'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
