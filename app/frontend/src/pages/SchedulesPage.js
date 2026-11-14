import React, { useState, useEffect, useCallback } from 'react';
import scheduleService from '../services/scheduleService';
import adService from '../services/adService';
import ScheduleList from '../components/schedules/ScheduleList';
import ScheduleForm from '../components/schedules/ScheduleForm';
import { Button } from 'components/ui/button';
import { useToast } from '../components/ui/toast';

const SchedulesPage = () => {
  const [schedules, setSchedules] = useState([]);
  const [ads, setAds] = useState([]);
  const [editingSchedule, setEditingSchedule] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const { toast } = useToast();

  const fetchSchedules = useCallback(async () => {
    try {
      const response = await scheduleService.getSchedules();
      setSchedules(response.data);
    } catch (error) {
      console.error('Error fetching schedules:', error);
      toast('Could not load schedules.', 'error');
    }
  }, [toast]);

  const fetchAds = useCallback(async () => {
    try {
      const response = await adService.getAds();
      setAds(response.data);
    } catch (error) {
      console.error('Error fetching ads:', error);
      toast('Could not load ads.', 'error');
    }
  }, [toast]);

  useEffect(() => {
    fetchSchedules();
    fetchAds();
  }, [fetchSchedules, fetchAds]);

  const handleFormSubmit = async (formData) => {
    try {
      if (editingSchedule) {
        await scheduleService.updateSchedule(editingSchedule.id, formData);
        toast('Schedule updated.', 'success');
      } else {
        await scheduleService.createSchedule(formData);
        toast('Schedule created.', 'success');
      }
      await fetchSchedules();
      setEditingSchedule(null);
      setShowForm(false);
    } catch (error) {
      console.error('Error submitting form:', error);
      toast(error.response?.data?.detail || 'Could not save the schedule.', 'error');
    }
  };

  const handleToggle = async (id, data) => {
    try {
      await scheduleService.updateSchedule(id, data);
      await fetchSchedules();
    } catch (error) {
      console.error('Error toggling schedule:', error);
      toast('Could not toggle the schedule.', 'error');
    }
  };

  const handleEdit = (schedule) => {
    setEditingSchedule(schedule);
    setShowForm(true);
  };

  const handleAddNew = () => {
    if (ads.length === 0) {
      toast('Please add at least one ad before creating a schedule.', 'info');
      return;
    }
    setEditingSchedule(null);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this schedule?')) {
      try {
        await scheduleService.deleteSchedule(id);
        await fetchSchedules();
        toast('Schedule deleted.', 'success');
      } catch (error) {
        console.error('Error deleting schedule:', error);
        toast('Could not delete the schedule.', 'error');
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold">Schedules Management</h2>
        <Button onClick={handleAddNew}>Add New Schedule</Button>
      </div>

      {showForm && (
        <ScheduleForm
          onSubmit={handleFormSubmit}
          ads={ads}
          initialData={editingSchedule}
        />
      )}

      <div className="mt-6">
        <ScheduleList schedules={schedules} onEdit={handleEdit} onDelete={handleDelete} onToggle={handleToggle} />
      </div>
    </div>
  );
};

export default SchedulesPage;
