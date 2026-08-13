import { useSelector, useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import type { RootState } from "@/store";
import { logout as logoutAction } from "@/store/slices/authSlice";

export function useAuth() {
  const auth = useSelector((state: RootState) => state.auth);
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const logout = () => {
    dispatch(logoutAction());
    navigate("/login");
  };

  return { ...auth, isAuthenticated: !!auth.accessToken, logout };
}
