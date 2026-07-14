import { defineStore } from 'pinia';
import { jwtDecode } from 'jwt-decode';
import api from '../services/api';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null,
    user: null,
    isAuthenticated: false,
  }),
  
  actions: {
    /**
     * Realiza o login do usuário enviando as credenciais para o backend FastAPI
     * @param {Object} credentials - Objeto contendo username e password
     */
    async login(credentials) {
      try {
        // O FastAPI com OAuth2PasswordRequestForm exige envio em formato x-www-form-urlencoded
        const formData = new URLSearchParams();
        formData.append('username', credentials.username);
        formData.append('password', credentials.password);

        // Envia as credenciais para o endpoint com o header explícito correspondente
        const response = await api.post('/api/v1/auth/login', formData, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        });
        
        // FastAPI retorna o token de acesso no campo access_token
        const { access_token } = response.data;
        
        // Decodifica o token JWT para extrair a identidade do usuário (campo sub)
        const decoded = jwtDecode(access_token);
        const user = {
          username: decoded.sub,
        };
        
        // Atualiza o estado da store
        this.token = access_token;
        this.user = user;
        this.isAuthenticated = true;
        
        // Salva os dados de autenticação no localStorage para persistência da sessão
        localStorage.setItem('token', access_token);
        localStorage.setItem('user', JSON.stringify(user));
        
        return { success: true };
      } catch (error) {
        console.error('Erro na ação de login:', error);
        throw error;
      }
    },
    
    /**
     * Limpa o estado da sessão e remove as credenciais do localStorage
     */
    logout() {
      // Limpa os dados na store Pinia
      this.token = null;
      this.user = null;
      this.isAuthenticated = false;
      
      // Remove do localStorage
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    },
    
    /**
     * Inicializa a store recuperando os dados persistidos no localStorage
     */
    init() {
      const token = localStorage.getItem('token');
      const userStr = localStorage.getItem('user');
      
      if (token && userStr) {
        try {
          this.token = token;
          this.user = JSON.parse(userStr);
          this.isAuthenticated = true;
        } catch (error) {
          console.error('Erro ao inicializar sessão a partir do localStorage:', error);
          this.logout();
        }
      }
    }
  }
});
