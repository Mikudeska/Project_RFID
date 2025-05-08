import axios from 'axios';

const API_URL = 'http://localhost:8000/api/person/';

export default {
    // CRUD Operations
    getPersons() {
        return axios.get(API_URL);
    },
    createPerson(data) {
        return axios.post(API_URL, data);
    },
    updatePerson(id, data) {
        return axios.put(`${API_URL}${id}/`, data);
    },
    deletePerson(id) {
        return axios.delete(`${API_URL}${id}/`);
    },
    bulkDelete(ids) {
        return axios.delete(`${API_URL}delete/`, { data: { ids } });
    }
};
