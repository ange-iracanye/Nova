import Navbar from "./Navbar";

export default function Layout({ children }) {

    return (

        <div className="
            min-h-screen
            bg-slate-950
            text-white
            overflow-x-hidden
        ">

            <Navbar />

            <main className="
                max-w-7xl
                mx-auto
                px-6
            ">

                {children}

            </main>

        </div>

    );
}