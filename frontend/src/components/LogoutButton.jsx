import { useNavigate } from "react-router-dom";

export default function LogoutButton() {

    const navigate = useNavigate();

    function logout() {

        localStorage.removeItem("nova_user");

        navigate("/login");

    }

    return (

        <button
            onClick={logout}
            className="
                text-gray-400
                hover:text-white
                transition
            "
        >
            Log out
        </button>

    );
}