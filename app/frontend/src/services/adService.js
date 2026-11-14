import api from './api';

const getAds = () => {
  return api.get('/ads/');
};

const getAd = (id) => {
  return api.get(`/ads/${id}`);
};

const createAd = (ad) => {
  return api.post('/ads/', ad);
};

const updateAd = (id, ad) => {
  return api.patch(`/ads/${id}`, ad);
};

const deleteAd = (id) => {
  return api.delete(`/ads/${id}`);
};

const generateAdText = (prompt) => {
  return api.post('/ads/generate-text', { prompt });
};

const publishAd = (id) => {
  return api.post(`/ads/${id}/publish`);
};

const getPublishHistory = (id) => {
  return api.get(`/ads/${id}/publish-history`);
};

const adService = {
  getAds,
  getAd,
  createAd,
  updateAd,
  deleteAd,
  generateAdText,
  publishAd,
  getPublishHistory,
};

export default adService;
