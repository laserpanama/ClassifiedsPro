import React, { useState, useEffect, useCallback } from 'react';
import adService from '../services/adService';
import accountService from '../services/accountService';
import AdList from '../components/ads/AdList';
import AdForm from '../components/ads/AdForm';
import { Button } from 'components/ui/button';
import { useToast } from '../components/ui/toast';

const AdsPage = () => {
  const [ads, setAds] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [editingAd, setEditingAd] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [publishingId, setPublishingId] = useState(null);
  const { toast } = useToast();

  const fetchAds = useCallback(async () => {
    try {
      const response = await adService.getAds();
      setAds(response.data);
    } catch (error) {
      console.error('Error fetching ads:', error);
      toast('Could not load ads.', 'error');
    }
  }, [toast]);

  const fetchAccounts = useCallback(async () => {
    try {
      const response = await accountService.getAccounts();
      setAccounts(response.data.filter(acc => acc.is_active)); // Only use active accounts
    } catch (error) {
      console.error('Error fetching accounts:', error);
      toast('Could not load accounts.', 'error');
    }
  }, [toast]);

  useEffect(() => {
    fetchAds();
    fetchAccounts();
  }, [fetchAds, fetchAccounts]);

  const handleFormSubmit = async (formData) => {
    try {
      if (editingAd) {
        await adService.updateAd(editingAd.id, formData);
        toast('Ad updated.', 'success');
      } else {
        await adService.createAd(formData);
        toast('Ad created.', 'success');
      }
      await fetchAds();
      setEditingAd(null);
      setShowForm(false);
    } catch (error) {
      console.error('Error submitting form:', error);
      toast(error.response?.data?.detail || 'Could not save the ad.', 'error');
    }
  };

  const handleEdit = (ad) => {
    setEditingAd(ad);
    setShowForm(true);
  };

  const handleAddNew = () => {
    if (accounts.length === 0) {
      toast('Please add at least one active account before creating an ad.', 'info');
      return;
    }
    setEditingAd(null);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this ad? Its schedules will be deleted too.')) {
      try {
        await adService.deleteAd(id);
        await fetchAds();
        toast('Ad deleted.', 'success');
      } catch (error) {
        console.error('Error deleting ad:', error);
        toast('Could not delete the ad.', 'error');
      }
    }
  };

  const handlePublish = async (id) => {
    setPublishingId(id);
    try {
      await adService.publishAd(id);
      toast('Ad publishing started in the background.', 'success');
    } catch (error) {
      console.error('Error publishing ad:', error);
      toast(error.response?.data?.detail || 'Could not start publishing.', 'error');
    } finally {
      setPublishingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold">Ads Management</h2>
        <Button onClick={handleAddNew}>Add New Ad</Button>
      </div>

      {showForm && (
        <AdForm
          onSubmit={handleFormSubmit}
          accounts={accounts}
          initialData={editingAd}
        />
      )}

      <div className="mt-6">
        <AdList ads={ads} onEdit={handleEdit} onDelete={handleDelete} onPublish={handlePublish} publishingId={publishingId} />
      </div>
    </div>
  );
};

export default AdsPage;
