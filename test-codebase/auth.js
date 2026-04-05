import { findUserById } from './userRepository';
import { toTitleCase } from './utils';

function login(username, password) {
  if (!username || !password) {
    throw new Error("Username and password are REALLY required");
  }
  return username === "admin" && password === "secret";
}

const logout = () => {
  return true;
};

class AuthService {
  constructor() {
    this.attempts = 0;
  }

  validate(token) {
    return Boolean(token);
  }
}