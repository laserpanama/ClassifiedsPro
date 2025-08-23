import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const AccountForm = ({ onSubmit, initialData = null }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  useEffect(() => {
    if (initialData) {
      setEmail(initialData.email || '');
      // Do not pre-fill password for security
    } else {
      // Reset form when there's no initial data (i.e., for creation)
      setEmail('');
      setPassword('');
    }
  }, [initialData]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = {
      email,
      wanuncios_password: password
    };
    // Only include password if it's being set/changed
    if (!password && initialData) {
      delete formData.wanuncios_password;
    }
    onSubmit(formData);
    // Only reset form if it's for creation
    if (!initialData) {
        setEmail('');
        setPassword('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4 border rounded-md">
      <h3 className="text-lg font-medium">{initialData ? 'Edit Account' : 'Create a New Account'}</h3>
      <div className="space-y-2">
        <Label htmlFor="email">Account Email</Label>
        <Input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="user@example.com"
          required
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="password">wanuncios.com Password</Label>
        <Input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          // Password is only strictly required for new accounts
          required={!initialData}
        />
        {initialData && <p className="text-xs text-muted-foreground">Leave blank to keep the current password.</p>}
      </div>
      <Button type="submit">{initialData ? 'Update Account' : 'Create Account'}</Button>
    </form>
  );
};

export default AccountForm;
