#!/usr/bin/env python3
"""
CRYPTONITA GNN - EXPERIMENTO 1: PREDICTOR PURO
=============================================

OBJETIVO: ¿Puede el GNN predecir movimientos mejor que random?

CONFIGURACIÓN:
- Input: Solo datos crypto (15 características ganadoras)  
- Output: Probabilidad [BAJISTA, NEUTRAL, ALCISTA] para cada ticker
- Target: Movimiento real del precio a 7 días
- Métrica principal: Accuracy de predicción
- Split temporal: 70% train / 15% val / 15% test

CRITERIO DE ÉXITO:
- Accuracy > 40% (baseline random = 33%)
- F1-score balanceado > 0.35
- Mejora consistente durante entrenamiento

EJECUTAR: python 04_experiment_01_predictor_puro.py
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import pandas as pd
import numpy as np
import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# Imports locales
script_dir = Path(__file__).parent
sys.path.append(str(script_dir))

try:
    from gnn_architecture import CryptonitaGNN, GraphDataProcessor
    logging.info("✅ Arquitectura GNN importada correctamente")
except ImportError as e:
    logging.error(f"❌ Error importando arquitectura: {e}")
    sys.exit(1)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'experiment_01_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

class Experiment01PredictorPuro:
    """
    EXPERIMENTO 1: GNN Predictor Puro
    
    El objetivo es establecer un baseline: ¿puede el GNN aprender
    a predecir direcciones de precio mejor que el azar?
    """
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.data_dir = self.script_dir / 'data'
        self.results_dir = self.script_dir / 'results' / 'experiment_01'
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración del experimento
        self.config = {
            'experiment_name': 'experiment_01_predictor_puro',
            'data_file': 'gnn_minimal_features.parquet',
            'prediction_horizon': 7,      # Predecir movimiento a 7 días
            'sequence_length': 20,        # Ventana temporal de entrada
            'movement_threshold': 0.02,   # 2% para definir BAJISTA/ALCISTA
            
            # Split temporal (CRÍTICO - no random)
            'train_ratio': 0.70,
            'val_ratio': 0.15,
            'test_ratio': 0.15,
            
            # Configuración del modelo
            'model_config': {
                'hidden_dim': 64,
                'lstm_layers': 2,
                'gnn_layers': 3,
                'num_heads': 8,
                'dropout': 0.3,
                'output_classes': 3  # BAJISTA(0), NEUTRAL(1), ALCISTA(2)
            },
            
            # Entrenamiento
            'training_config': {
                'epochs': 200,
                'learning_rate': 0.001,
                'weight_decay': 1e-4,
                'patience': 30,
                'min_epochs': 50
            }
        }
        
        self.experiment_log = {
            'start_time': datetime.now().isoformat(),
            'config': self.config,
            'results': {}
        }
        
        logging.info("🚀 EXPERIMENTO 1: Predictor Puro inicializado")
        logging.info(f"   🎯 Objetivo: Accuracy > 40% (vs 33% random)")
        logging.info(f"   📊 Horizonte predicción: {self.config['prediction_horizon']} días")
        logging.info(f"   📅 Umbral movimiento: ±{self.config['movement_threshold']*100}%")
    
    def load_and_prepare_data(self):
        """
        Carga y prepara los datos con split temporal estricto
        """
        logging.info("📊 Cargando y preparando datos...")
        
        try:
            # Cargar datos
            data_path = self.data_dir / self.config['data_file']
            df = pd.read_parquet(data_path)
            
            logging.info(f"   ✅ Datos cargados: {df.shape}")
            logging.info(f"   🪙 Tickers: {df['ticker'].nunique()}")
            logging.info(f"   📅 Rango: {df['timestamp'].min()} - {df['timestamp'].max()}")
            
            # Crear targets basados en movimientos futuros
            df_with_targets = self.create_movement_targets(df)
            
            # Split temporal (CRÍTICO)
            train_df, val_df, test_df = self.temporal_split(df_with_targets)
            
            # Preparar features
            feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            feature_cols = [col for col in feature_cols if col != 'target']
            
            logging.info(f"   🎯 Features utilizadas: {len(feature_cols)}")
            logging.info(f"   📊 Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
            
            return {
                'train_df': train_df,
                'val_df': val_df, 
                'test_df': test_df,
                'feature_cols': feature_cols
            }
            
        except Exception as e:
            logging.error(f"❌ Error preparando datos: {e}")
            raise
    
    def create_movement_targets(self, df):
        """
        Crea targets basados en movimientos de precio futuros
        
        Target logic:
        - BAJISTA (0): future_return < -threshold
        - NEUTRAL (1): -threshold <= future_return <= threshold  
        - ALCISTA (2): future_return > threshold
        """
        logging.info("🎯 Creando targets de movimiento...")
        
        df_with_targets = []
        horizon = self.config['prediction_horizon']
        threshold = self.config['movement_threshold']
        
        for ticker in df['ticker'].unique():
            ticker_data = df[df['ticker'] == ticker].sort_values('timestamp').copy()
            
            if len(ticker_data) < horizon + self.config['sequence_length']:
                logging.warning(f"   ⚠️  {ticker}: datos insuficientes, omitiendo")
                continue
            
            # Calcular retorno futuro
            ticker_data['future_price'] = ticker_data['close'].shift(-horizon)
            ticker_data['future_return'] = (
                ticker_data['future_price'] / ticker_data['close'] - 1
            )
            
            # Crear targets
            conditions = [
                ticker_data['future_return'] < -threshold,  # BAJISTA
                (ticker_data['future_return'] >= -threshold) & 
                (ticker_data['future_return'] <= threshold),   # NEUTRAL
                ticker_data['future_return'] > threshold     # ALCISTA
            ]
            choices = [0, 1, 2]
            ticker_data['target'] = np.select(conditions, choices, default=1)
            
            # Eliminar filas sin target válido
            ticker_data = ticker_data.dropna(subset=['future_return', 'target'])
            df_with_targets.append(ticker_data)
        
        # Combinar todos los tickers
        result_df = pd.concat(df_with_targets, ignore_index=True)
        
        # Estadísticas de targets
        target_counts = result_df['target'].value_counts().sort_index()
        target_pcts = (target_counts / len(result_df) * 100).round(1)
        
        logging.info("   ✅ Targets creados:")
        logging.info(f"      BAJISTA(0): {target_counts.get(0, 0)} ({target_pcts.get(0, 0)}%)")
        logging.info(f"      NEUTRAL(1): {target_counts.get(1, 0)} ({target_pcts.get(1, 0)}%)")
        logging.info(f"      ALCISTA(2): {target_counts.get(2, 0)} ({target_pcts.get(2, 0)}%)")
        
        self.experiment_log['target_distribution'] = {
            'BAJISTA': int(target_counts.get(0, 0)),
            'NEUTRAL': int(target_counts.get(1, 0)),
            'ALCISTA': int(target_counts.get(2, 0))
        }
        
        return result_df
    
    def temporal_split(self, df):
        """
        Split temporal estricto - NO ALEATORIO
        """
        logging.info("📅 Realizando split temporal...")
        
        # Ordenar por fecha
        df = df.sort_values('timestamp')
        dates = sorted(df['timestamp'].unique())
        n_dates = len(dates)
        
        # Calcular puntos de corte
        train_end_idx = int(n_dates * self.config['train_ratio'])
        val_end_idx = int(n_dates * (self.config['train_ratio'] + self.config['val_ratio']))
        
        train_end_date = dates[train_end_idx]
        val_end_date = dates[val_end_idx]
        
        # Crear splits
        train_df = df[df['timestamp'] <= train_end_date].copy()
        val_df = df[(df['timestamp'] > train_end_date) & 
                   (df['timestamp'] <= val_end_date)].copy()
        test_df = df[df['timestamp'] > val_end_date].copy()
        
        logging.info("   ✅ Split temporal completado:")
        logging.info(f"      Train: {train_end_date.date()} ({len(train_df)} samples)")
        logging.info(f"      Val: {val_end_date.date()} ({len(val_df)} samples)")
        logging.info(f"      Test: desde {val_end_date.date()} ({len(test_df)} samples)")
        
        # Verificar que cada split tiene todas las clases
        for split_name, split_df in [('Train', train_df), ('Val', val_df), ('Test', test_df)]:
            target_counts = split_df['target'].value_counts().sort_index()
            logging.info(f"      {split_name} targets: {dict(target_counts)}")
        
        return train_df, val_df, test_df
    
    def prepare_graph_data(self, df, feature_cols, split_name=""):
        """
        Convierte DataFrame en datos de grafo para el GNN
        """
        logging.info(f"🔄 Preparando datos de grafo ({split_name})...")
        
        try:
            processor = GraphDataProcessor(
                sequence_length=self.config['sequence_length']
            )
            
            # Preparar secuencias temporales
            sequences, valid_tickers = processor.prepare_sequences(df, feature_cols)
            
            # Extraer targets correspondientes
            targets = self.extract_targets_for_tickers(df, valid_tickers)
            
            # Crear estructura de grafo basada en correlaciones
            returns_data = self.extract_returns_matrix(df, valid_tickers)
            edge_index, edge_weights = processor.create_correlation_edges(
                returns_data, threshold=0.15
            )
            
            logging.info(f"   ✅ Grafo {split_name} preparado:")
            logging.info(f"      Secuencias: {sequences.shape}")
            logging.info(f"      Targets: {targets.shape}")
            logging.info(f"      Distribución: {np.bincount(targets)}")
            logging.info(f"      Aristas: {edge_index.shape[1]}")
            logging.info(f"      Tickers: {valid_tickers}")
            
            return {
                'sequences': torch.FloatTensor(sequences),
                'targets': torch.LongTensor(targets),
                'edge_index': torch.LongTensor(edge_index),
                'edge_weights': torch.FloatTensor(edge_weights),
                'tickers': valid_tickers,
                'processor': processor
            }
            
        except Exception as e:
            logging.