import axios from 'axios';
import router from '../router';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor de Requisição: Injeta o token se existir no localStorage
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor de Resposta: Redireciona e limpa a sessão em caso de erro 401 (Não Autorizado)
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      // Limpa os dados de autenticação do localStorage
      localStorage.removeItem('token');
      localStorage.removeItem('user');

      // Redireciona para a tela de login via Vue Router
      router.push('/login');
    }
    return Promise.reject(error);
  }
);

export default api;
