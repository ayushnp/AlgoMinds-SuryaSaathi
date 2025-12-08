// Renamed file: frontend/app/screens/VerificationFormScreen.js

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

// --- SIMULATION HELPERS ---
// NOTE: In a real Expo app, replace these with actual Expo ImagePicker and Location calls
const mockGetLocation = async () => ({ latitude: 28.6139, longitude: 77.2090, name: 'Current Location' });
const mockPickImage = async (key) => ({ uri: `/mock/path/to/${key}.jpg`, name: `${key}_${Date.now()}.jpg`, mimeType: 'image/jpeg' });
// --------------------------

export default function VerificationFormScreen({ navigation, route }) {
  // Get Application ID from the route parameters
  const { applicationId } = route.params || {};

  const [formData, setFormData] = useState({
    application_id: applicationId || '', // Can be manually entered if not navigated from Step 1
    registered_lat: '',
    registered_lon: '',
  });
  const [photos, setPhotos] = useState({
    wide_rooftop_photo: null,
    serial_number_photo: null,
    inverter_photo: null,
  });
  const [loading, setLoading] = useState(false);

  const handleFieldChange = (key, value) => {
    setFormData({ ...formData, [key]: value });
  };

  const handleGetLocation = async () => {
    try {
      const { latitude, longitude } = await mockGetLocation();
      setFormData(prev => ({
        ...prev,
        registered_lat: latitude.toString(),
        registered_lon: longitude.toString()
      }));
      Alert.alert('Location Captured', `Lat: ${latitude}, Lon: ${longitude}`);
    } catch (e) {
      Alert.alert('Error', 'Could not get location. Check permissions.');
    }
  };

  const handlePickPhoto = async (key) => {
    try {
      const result = await mockPickImage(key);
      if (result) {
        setPhotos(prev => ({ ...prev, [key]: result }));
        Alert.alert('Photo Selected', result.name);
      }
    } catch (e) {
      Alert.alert('Error', 'Could not pick photo.');
    }
  };

  const validateAndSubmit = () => {
    const isIdValid = formData.application_id && formData.application_id.length > 5;
    const isGpsValid = formData.registered_lat && formData.registered_lon;
    const isPhotosValid = Object.values(photos).every(photo => photo !== null);

    if (!isIdValid) {
        Alert.alert('Error', 'Please enter a valid Application ID.');
        return;
    }
    if (!isGpsValid) {
      Alert.alert('Error', 'Please capture or enter GPS coordinates.');
      return;
    }
    if (!isPhotosValid) {
      Alert.alert('Error', 'Please upload all three required photos.');
      return;
    }

    handleSubmit();
  };


  const handleSubmit = async () => {
    setLoading(true);

    const data = new FormData();

    // 1. Append Application ID
    data.append('application_id', formData.application_id);

    // 2. Append GPS data
    data.append('registered_lat', parseFloat(formData.registered_lat));
    data.append('registered_lon', parseFloat(formData.registered_lon));

    // 3. Append photo files
    for (const [key, photo] of Object.entries(photos)) {
      // Create a file object suitable for fetch/axios FormData
      const file = {
        uri: photo.uri,
        name: photo.name,
        type: photo.mimeType,
      };
      data.append(key, file);
    }

    try {
      await applicationAPI.submitVerification(data);

      Alert.alert(
        'Submission Complete!',
        `Verification for Application ID ${formData.application_id} has started.`
      );

      navigation.navigate('ApplicationList');
    } catch (error) {
      console.error(error);
      const detail = error.detail || (error.message ? `Error: ${error.message}` : 'Failed to submit verification');
      Alert.alert('Submission Failed', detail);
    } finally {
      setLoading(false);
    }
  };

  const PhotoPicker = ({ label, photoKey }) => (
    <View style={styles.photoContainer}>
      <Text style={styles.photoLabel}>{label} *</Text>
      <TouchableOpacity
        style={styles.photoButton}
        onPress={() => handlePickPhoto(photoKey)}
      >
        <Text style={styles.photoButtonText}>
          {photos[photoKey] ? `✅ Selected: ${photos[photoKey].name.substring(0, 20)}...` : 'Upload Photo'}
        </Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Verification Submission (Step 2)</Text>

      <TextInput
        style={styles.input}
        placeholder="Enter Application ID *"
        value={formData.application_id}
        onChangeText={(text) => handleFieldChange('application_id', text)}
        editable={!applicationId} // Disable if ID was passed from Step 1
      />

      <Text style={styles.header}>Capture Site Location *</Text>

      {/* --- Location Section --- */}
      <View style={styles.locationSection}>
        <TextInput
            style={[styles.input, styles.halfInput]}
            placeholder="Latitude"
            value={formData.registered_lat}
            onChangeText={(text) => handleFieldChange('registered_lat', text)}
            keyboardType="numeric"
        />
        <TextInput
            style={[styles.input, styles.halfInput]}
            placeholder="Longitude"
            value={formData.registered_lon}
            onChangeText={(text) => handleFieldChange('registered_lon', text)}
            keyboardType="numeric"
        />
      </View>
      <TouchableOpacity style={styles.locationButton} onPress={handleGetLocation} disabled={loading}>
          <Text style={styles.buttonText}>Capture Current GPS Location</Text>
      </TouchableOpacity>

      {/* --- Photo Uploads --- */}
      <Text style={styles.header}>Required Verification Photos *</Text>
      <PhotoPicker label="Wide Rooftop Photo" photoKey="wide_rooftop_photo" />
      <PhotoPicker label="Serial Number Close-up" photoKey="serial_number_photo" />
      <PhotoPicker label="Inverter Installation Photo" photoKey="inverter_photo" />

      <TouchableOpacity
        style={[styles.button, loading && styles.buttonDisabled]}
        onPress={validateAndSubmit}
        disabled={loading}
      >
        <Text style={styles.buttonText}>
          {loading ? 'Submitting Verification...' : 'Submit Verification'}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: '#f5f5f5' },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 10, color: '#FF9800' },
  subtitle: { fontSize: 16, color: '#FF9800', marginBottom: 20, fontWeight: 'bold' },
  header: { fontSize: 18, fontWeight: 'bold', color: '#333', marginTop: 10, marginBottom: 15, borderBottomWidth: 1, borderBottomColor: '#ddd', paddingBottom: 5 },
  input: { backgroundColor: 'white', borderWidth: 1, borderColor: '#ddd', padding: 15, marginBottom: 15, borderRadius: 8, fontSize: 16 },
  locationSection: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 15 },
  halfInput: { width: '48%', marginBottom: 0 },
  locationButton: { backgroundColor: '#007BFF', padding: 15, borderRadius: 8, alignItems: 'center', marginBottom: 20 },
  photoContainer: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 },
  photoLabel: { fontSize: 16, color: '#333', width: '40%' },
  photoButton: { backgroundColor: '#4CAF50', padding: 10, borderRadius: 8, alignItems: 'center', width: '55%' },
  photoButtonText: { color: 'white', fontSize: 14, fontWeight: 'bold' },
  button: { backgroundColor: '#FF9800', padding: 15, borderRadius: 8, alignItems: 'center', marginTop: 20, marginBottom: 30 },
  buttonDisabled: { backgroundColor: '#FFA733' },
  buttonText: { color: 'white', fontSize: 18, fontWeight: 'bold' },
});