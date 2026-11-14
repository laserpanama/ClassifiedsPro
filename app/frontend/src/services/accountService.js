import api from './api';

const getAccounts = () => {
  return api.get('/accounts/');
};

const getAccount = (id) => {
  return api.get(`/accounts/${id}`);
};

const createAccount = (account) => {
  return api.post('/accounts/', account);
};

const updateAccount = (id, account) => {
  return api.patch(`/accounts/${id}`, account);
};

const deleteAccount = (id) => {
  return api.delete(`/accounts/${id}`);
};

const accountService = {
  getAccounts,
  getAccount,
  createAccount,
  updateAccount,
  deleteAccount,
};

export default accountService;
