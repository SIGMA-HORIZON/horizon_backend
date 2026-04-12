import React from "react";
import Image from "next/image";

const Accueil = () => {
  return (
    <section
      id="accueil" >

      <div className="pt-20 flex items-center justify-center display-flex space-x-4">

        <div>   page d'accueil Horizon <br /></div> <br />
        <div> <button className="bg-blue-400 ">  <a href="connexion">Connexion</a> </button></div>
        <div> <button className="bg-blue-400 ">  <a href="dashboad-admin">dashboad</a> </button></div>
        <div> <button className="bg-blue-400 ">  <a href="mon-profil-use">profil</a> </button></div>
        <div> <button className="bg-blue-400 ">  <a href="mes-vms"> liste vms</a> </button></div>
      </div>
    </section>
  );
};

export default Accueil;
