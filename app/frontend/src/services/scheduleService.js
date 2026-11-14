import api from './api';

const getSchedules = () => {
  return api.get('/schedules/');
};

const getSchedule = (id) => {
  return api.get(`/schedules/${id}`);
};

const createSchedule = (schedule) => {
  return api.post('/schedules/', schedule);
};

const updateSchedule = (id, schedule) => {
  return api.patch(`/schedules/${id}`, schedule);
};

const deleteSchedule = (id) => {
  return api.delete(`/schedules/${id}`);
};

const scheduleService = {
  getSchedules,
  getSchedule,
  createSchedule,
  updateSchedule,
  deleteSchedule,
};

export default scheduleService;
