import {
  createAsyncThunk,
  createSlice,
  isFulfilled,
  isPending,
  isRejected,
  PayloadAction,
} from "@reduxjs/toolkit";
import {
  AuthUser,
  clearToken,
  getMe,
  login as apiLogin,
  register as apiRegister,
  saveToken,
} from "@/lib/api";

interface AuthState {
  user: AuthUser | null;
  token: string | null;
  status: "anonymous" | "authenticating" | "authenticated";
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  token: null,
  status: "anonymous",
  error: null,
};

export const login = createAsyncThunk(
  "auth/login",
  async (credentials: { email: string; password: string }) => {
    const response = await apiLogin(credentials.email, credentials.password);
    saveToken(response.data.token);
    const user = await getMe();
    return { user, token: response.data.token };
  },
);

export const register = createAsyncThunk(
  "auth/register",
  async (credentials: { email: string; username: string; password: string }) => {
    const response = await apiRegister(
      credentials.email,
      credentials.username,
      credentials.password,
    );
    saveToken(response.data.token);
    const user = await getMe();
    return { user, token: response.data.token };
  },
);

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setUser(state, action: PayloadAction<{ user: AuthUser; token: string }>) {
      state.user = action.payload.user;
      state.token = action.payload.token;
      state.status = "authenticated";
      state.error = null;
    },
    logout(state) {
      clearToken();
      state.user = null;
      state.token = null;
      state.status = "anonymous";
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(isPending(login, register), (state) => {
        state.status = "authenticating";
        state.error = null;
      })
      .addMatcher(isFulfilled(login, register), (state, action) => {
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.status = "authenticated";
        state.error = null;
      })
      .addMatcher(isRejected(login, register), (state, action) => {
        state.status = "anonymous";
        state.error = action.error.message ?? "Authentication failed";
      });
  },
});

export const { setUser, logout } = authSlice.actions;

export default authSlice.reducer;
