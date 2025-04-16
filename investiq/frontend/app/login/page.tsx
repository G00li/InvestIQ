'use client';

import React from "react";
import Image from "next/image";
import { motion } from "framer-motion";

export default function Login() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 flex">
      {/* Conteúdo Principal - Lado Esquerdo */}
      <motion.div 
        className="flex-1 flex items-center justify-center p-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="text-center">
          <motion.h1 
            className="text-4xl md:text-6xl font-bold text-white mb-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            Bem-vindo Novamente!
          </motion.h1>
          <motion.p 
            className="text-xl text-gray-300 mb-8"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            Continue sua jornada de investimentos inteligentes
          </motion.p>
        </div>
      </motion.div>

      {/* Botões de Login - Lado Direito */}
      <motion.div 
        className="w-96 bg-gray-800 p-8 flex flex-col justify-center space-y-4"
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5, delay: 0.6 }}
      >
        <h2 className="text-2xl font-bold text-white mb-6 text-center">
          Entrar com
        </h2>
        
        <motion.button
          className="flex items-center justify-center space-x-3 w-full bg-white text-gray-800 px-6 py-3 rounded-lg hover:bg-gray-100 transition-colors"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <Image
            src="/icons/login/Gmail-icon.svg"
            alt="Gmail"
            width={24}
            height={24}
          />
          <span>Continuar com Gmail</span>
        </motion.button>

        <motion.button
          className="flex items-center justify-center space-x-3 w-full bg-gray-900 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <Image
            src="/icons/login/Github-icon.svg"
            alt="GitHub"
            width={24}
            height={24}
          />
          <span>Continuar com GitHub</span>
        </motion.button>

        <p className="text-gray-400 text-center mt-6">
          Não tem uma conta?{" "}
          <a href="/register" className="text-blue-500 hover:text-blue-400">
            Registre-se
          </a>
        </p>
      </motion.div>
    </div>
  );
}

