export interface User {
  id: number;
  username: string;
  role: 'admin' | 'operatore' | 'user';
  person_id?: number | null;
}

export const auth = {
  getToken: (): string | null => {
    return localStorage.getItem('token');
  },

  setToken: (token: string): void => {
    localStorage.setItem('token', token);
  },

  removeToken: (): void => {
    localStorage.removeItem('token');
  },

  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('token');
  },

  getUser: (): User | null => {
    const userStr = localStorage.getItem('user');
    if (!userStr) return null;
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  },

  setUser: (user: User): void => {
    localStorage.setItem('user', JSON.stringify({ 
      id: user.id, 
      username: user.username, 
      role: user.role,
      person_id: user.person_id 
    }));
  },

  removeUser: (): void => {
    localStorage.removeItem('user');
  },

  logout: (): void => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
};

