import React, { useState, useEffect, useCallback } from 'react';
import accountService from '../services/accountService';
import AccountList from '../components/accounts/AccountList';
import AccountForm from '../components/accounts/AccountForm';
import { Button } from 'components/ui/button';
import { useToast } from '../components/ui/toast';

const AccountsPage = () => {
  const [accounts, setAccounts] = useState([]);
  const [editingAccount, setEditingAccount] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const { toast } = useToast();

  const fetchAccounts = useCallback(async () => {
    try {
      const response = await accountService.getAccounts();
      setAccounts(response.data);
    } catch (error) {
      console.error('Error fetching accounts:', error);
      toast('Could not load accounts.', 'error');
    }
  }, [toast]);

  useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  const handleFormSubmit = async (formData) => {
    try {
      if (editingAccount) {
        await accountService.updateAccount(editingAccount.id, formData);
        toast('Account updated.', 'success');
      } else {
        await accountService.createAccount(formData);
        toast('Account created.', 'success');
      }
      await fetchAccounts();
      setEditingAccount(null);
      setShowForm(false);
    } catch (error) {
      console.error('Error submitting form:', error);
      toast(error.response?.data?.detail || 'Could not save the account.', 'error');
    }
  };

  const handleEdit = (account) => {
    setEditingAccount(account);
    setShowForm(true);
  };

  const handleAddNew = () => {
    setEditingAccount(null);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this account? Its ads and schedules will be deleted too.')) {
      try {
        await accountService.deleteAccount(id);
        await fetchAccounts();
        toast('Account deleted.', 'success');
      } catch (error) {
        console.error('Error deleting account:', error);
        toast('Could not delete the account.', 'error');
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold">Accounts Management</h2>
        <Button onClick={handleAddNew}>Add New Account</Button>
      </div>

      {showForm && (
        <AccountForm
          onSubmit={handleFormSubmit}
          initialData={editingAccount}
        />
      )}

      <div className="mt-6">
        <AccountList accounts={accounts} onEdit={handleEdit} onDelete={handleDelete} />
      </div>
    </div>
  );
};

export default AccountsPage;
