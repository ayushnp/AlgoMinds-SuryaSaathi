// In frontend/app/screens/HomeScreen.js

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { removeToken } from '../utils/auth';

export default function HomeScreen({ navigation }) {
  const handleLogout = async () => {
    await removeToken();
    navigation.replace('Auth');
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Welcome to Suryamitra</Text>
      
      <TouchableOpacity
        style={styles.card}
        // CORRECTED: Navigate to the new InitialApplicationForm screen
        onPress={() => navigation.navigate('InitialApplicationForm')} 
      >
        <Text style={styles.cardTitle}>New Application</Text>
        <Text style={styles.cardDescription}>Submit the initial solar subsidy application details</Text>
      </TouchableOpacity>
      
      {/* Optionally add a direct link to verification for existing applications */}
      <TouchableOpacity
        style={styles.card}
        onPress={() => navigation.navigate('VerificationForm')}
      >
        <Text style={styles.cardTitle}>Submit Verification Photos</Text>
        <Text style={styles.cardDescription}>Upload post-installation photos using an existing Application ID</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.card}
        onPress={() => navigation.navigate('ApplicationList')}
      >
        <Text style={styles.cardTitle}>My Applications</Text>
        <Text style={styles.cardDescription}>View your submitted applications</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>
    </View>
  );
}

// ... (keep existing styles) ...
const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 30,
    color: '#333',
  },
  card: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 10,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FF9800',
    marginBottom: 5,
  },
  cardDescription: {
    fontSize: 14,
    color: '#666',
  },
  logoutButton: {
    marginTop: 30,
    padding: 15,
    backgroundColor: '#f44336',
    borderRadius: 8,
    alignItems: 'center',
  },
  logoutText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
});