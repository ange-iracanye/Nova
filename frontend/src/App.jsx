import {
    BrowserRouter,
    Routes,
    Route,
    useLocation
} from "react-router-dom";

import Home from "./pages/Home";
import Chat from "./pages/Chat";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";

import {
    useEffect,
    useRef,
    useState
} from "react";


// =====================================
// REMEMBER LAST LEARNING PAGE
// =====================================

function RouteMemory() {

    const location =
        useLocation();


    useEffect(() => {

        const pathname =
            location.pathname;


        const currentRoute =
            pathname +
            location.search;


        const learningRoutes = [
            "/chat",
            "/dashboard"
        ];


        const shouldRemember =
            learningRoutes.some(
                route =>
                    pathname === route
            );


        if (shouldRemember) {

            localStorage.setItem(
                "nova_last_route",
                currentRoute
            );

        }

    }, [
        location.pathname,
        location.search
    ]);


    return null;

}


// =====================================
// PAGE TRANSITION
// =====================================

function PageTransition({
    children
}) {

    const location =
        useLocation();


    const previousPath =
        useRef(
            location.pathname
        );


    const [
        animate,
        setAnimate
    ] = useState(false);


    const [
        direction,
        setDirection
    ] = useState(
        "forward"
    );


    const firstRender =
        useRef(true);


    useEffect(() => {

        if (
            firstRender.current
        ) {

            firstRender.current =
                false;


            previousPath.current =
                location.pathname;


            return;

        }


        const oldPath =
            previousPath.current;


        const newPath =
            location.pathname;


        if (
            newPath === "/" &&
            oldPath !== "/"
        ) {

            setDirection(
                "back"
            );

        } else {

            setDirection(
                "forward"
            );

        }


        previousPath.current =
            newPath;


        setAnimate(
            true
        );


        const timer =
            setTimeout(() => {

                setAnimate(
                    false
                );

            }, 650);


        return () => {

            clearTimeout(
                timer
            );

        };

    }, [
        location.pathname,
        location.search
    ]);


    return (

        <div
            className={`
                nova-page

                ${
                    animate

                        ? direction === "back"

                            ? "nova-transition-back"

                            : "nova-transition-forward"

                        : ""
                }
            `}
        >

            {children}

        </div>

    );

}


// =====================================
// APP CONTENT
// =====================================

function AppContent() {

    return (

        <>

            <RouteMemory />


            <PageTransition>

                <Routes>

                    {/* HOME */}

                    <Route
                        path="/"
                        element={
                            <Home />
                        }
                    />


                    {/* CHAT */}

                    <Route
                        path="/chat"
                        element={
                            <Chat />
                        }
                    />


                    {/* DASHBOARD */}

                    <Route
                        path="/dashboard"
                        element={
                            <Dashboard />
                        }
                    />


                    {/* SETTINGS */}

                    <Route
                        path="/settings"
                        element={
                            <Settings />
                        }
                    />


                    {/* LOGIN */}

                    <Route
                        path="/login"
                        element={
                            <Login />
                        }
                    />


                    {/* REGISTER */}

                    <Route
                        path="/register"
                        element={
                            <Register />
                        }
                    />


                    {/* NOT FOUND */}

                    <Route
                        path="*"
                        element={
                            <NotFound />
                        }
                    />

                </Routes>

            </PageTransition>


            {/* =================================
                GLOBAL STYLES
            ================================= */}

            <style>{`

                html {

                    background:
                        #020617;

                }


                body {

                    margin: 0;

                    background:
                        #020617;

                    color:
                        white;

                    overflow-x: hidden;

                }


                #root {

                    min-height: 100vh;

                    background:
                        #020617;

                    overflow-x: hidden;

                }


                .nova-page {

                    position: relative;

                    min-height: 100vh;

                    width: 100%;

                    background:
                        #020617;

                }


                .nova-transition-forward {

                    animation:
                        novaRevealRight
                        0.62s
                        cubic-bezier(
                            0.22,
                            1,
                            0.36,
                            1
                        );

                    transform-origin:
                        center center;

                    will-change:
                        transform,
                        filter,
                        clip-path;

                }


                @keyframes novaRevealRight {

                    0% {

                        clip-path:
                            inset(
                                0 0 0 18%
                            );

                        transform:
                            scale(0.975)
                            translateX(18px);

                        filter:
                            blur(5px);

                    }


                    35% {

                        clip-path:
                            inset(
                                0 0 0 7%
                            );

                        transform:
                            scale(0.99)
                            translateX(5px);

                        filter:
                            blur(2px);

                    }


                    70% {

                        clip-path:
                            inset(
                                0 0 0 1%
                            );

                        transform:
                            scale(1.002)
                            translateX(0);

                        filter:
                            blur(0);

                    }


                    100% {

                        clip-path:
                            inset(
                                0 0 0 0
                            );

                        transform:
                            scale(1)
                            translateX(0);

                        filter:
                            blur(0);

                    }

                }


                .nova-transition-back {

                    animation:
                        novaRevealLeft
                        0.62s
                        cubic-bezier(
                            0.22,
                            1,
                            0.36,
                            1
                        );

                    transform-origin:
                        center center;

                    will-change:
                        transform,
                        filter,
                        clip-path;

                }


                @keyframes novaRevealLeft {

                    0% {

                        clip-path:
                            inset(
                                0 18% 0 0
                            );

                        transform:
                            scale(0.975)
                            translateX(-18px);

                        filter:
                            blur(5px);

                    }


                    35% {

                        clip-path:
                            inset(
                                0 7% 0 0
                            );

                        transform:
                            scale(0.99)
                            translateX(-5px);

                        filter:
                            blur(2px);

                    }


                    70% {

                        clip-path:
                            inset(
                                0 1% 0 0
                            );

                        transform:
                            scale(1.002)
                            translateX(0);

                        filter:
                            blur(0);

                    }


                    100% {

                        clip-path:
                            inset(
                                0 0 0 0
                            );

                        transform:
                            scale(1)
                            translateX(0);

                        filter:
                            blur(0);

                    }

                }


                @media (
                    prefers-reduced-motion: reduce
                ) {

                    .nova-transition-forward,
                    .nova-transition-back {

                        animation:
                            none !important;

                    }

                }

            `}</style>

        </>

    );

}


// =====================================
// ROOT
// =====================================

function App() {

    return (

        <BrowserRouter>

            <AppContent />

        </BrowserRouter>

    );

}


export default App;
