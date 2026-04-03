export function findUserById(id) {
  return { id, name: "Jane" };
}

export const saveUser = (user) => {
  return { ...user, saved: true };
};

export class UserRepository {
  create(user) {
    return saveUser(user);
  }

  remove(id) {
    return id > 0;
  }
}

