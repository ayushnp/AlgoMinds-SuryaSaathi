import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
} from 'react-native';
import { applicationAPI } from '../services/api';

export default function ApplicationFormScreen({ navigation }) {
  const [formData, setFormData] = useState({
    applicant_name: '',
    address: '',
    system_capacity: '',
    installer_name: '',
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!formData.applicant_name || !formData.address || !formData.system_capacity) {
      Alert.alert('Error', 'Please fill all required fields');
      return;
    }

    setLoading(true);
    try {
      await applicationAPI.create({
        ...formData,
        system_capacity: parseFloat(formData.system_capacity),
      });
      Alert.alert('Success', 'Application submitted successfully!');
      navigation.goBack();
    } catch (error) {
      Alert.alert('Error', error.detail || 'Failed to submit application');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>New Application</Text>

      <TextInput
        style={styles.input}
        placeholder="Applicant Name *"
        value={formData.applicant_name}
        onChangeText={(text) => setFormData({ ...formData, applicant_name: text })}
      />

      <TextInput
        style={styles.input}
        placeholder="Address *"
        value={formData.address}
        onChangeText={(text) => setFormData({ ...formData, address: text })}
        multiline
        numberOfLines={3}
      />

      <TextInput
        style={styles.input}
        placeholder="System Capacity (kW) *"
        value={formData.system_capacity}
        onChangeText={(text) => setFormData({ ...formData, system_capacity: text })}
        keyboardType="decimal-pad"
      />

      <TextInput
        style={styles.input}
        placeholder="Installer Name"
        value={formData.installer_name}
        onChangeText={(text) => setFormData({ ...formData, installer_name: text })}
      />

      <TouchableOpacity
        style={styles.button}
        onPress={handleSubmit}
        disabled={loading}
      >
        <Text style={styles.buttonText}>
          {loading ? 'Submitting...' : 'Submit Application'}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    color: '#333',
  },
  input: {
    backgroundColor: 'white',
    borderWidth: 1,
    borderColor: '#ddd',
    padding: 15,
    marginBottom: 15,
    borderRadius: 8,
    fontSize: 16,
  },
  button: {
    backgroundColor: '#FF9800',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 30,
  },
  buttonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
});
