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
// NEW IMPORTS FOR PRODUCTION
import * as Location from 'expo-location';
import * as ImagePicker from 'expo-image-picker';

import { applicationAPI } from '../services/api';


export default function VerificationFormScreen({ navigation, route }) {
  // Get Application ID from the route parameters (passed from Step 1)
  const { applicationId } = route.params || {};

  const [formData, setFormData] = useState({
    application_id: applicationId || '',
    registered_lat: '', // State for Latitude (will be auto-filled or manual)
    registered_lon: '', // State for Longitude (will be auto-filled or manual)
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

  // --- PRODUCTION GPS LOCATION CAPTURE ---
  const handleGetLocation = async () => {
    setLoading(true);
    try {
      // 1. Request Foreground Location Permission
      let { status: foregroundStatus } = await Location.requestForegroundPermissionsAsync();

      if (foregroundStatus !== 'granted') {
        Alert.alert('Permission Denied', 'Please grant location access to capture site coordinates.');
        return;
      }

      // 2. Get Current Position with High Accuracy
      let location = await Location.getCurrentPositionAsync({
          accuracy: Location.Accuracy.BestForNavigation,
          mayShareAddress: true // Recommended for better metadata/geocoding
      });

      const { latitude, longitude } = location.coords;

      // 3. Update State/Input fields
      setFormData(prev => ({
        ...prev,
        registered_lat: latitude.toString(),
        registered_lon: longitude.toString()
      }));

      Alert.alert('Location Captured', `Lat: ${latitude}, Lon: ${longitude}`);

    } catch (e) {
      console.error("Location Error:", e);
      Alert.alert('Error', 'Failed to get location. Ensure GPS is enabled and permissions are granted.');
    } finally {
        setLoading(false);
    }
  };

  // --- PRODUCTION CAMERA/IMAGE PICKER CAPTURE ---
  const handlePickPhoto = async (key) => {
    // 1. Request Camera Permission (Camera is best for reliable EXIF data)
    const { status } = await ImagePicker.requestCameraPermissionsAsync();

    if (status !== 'granted') {
        Alert.alert('Permission Denied', 'Camera permission is required to capture verification photos.');
        return;
    }

    try {
      // 2. Launch Camera
      let result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: false,
        quality: 0.7,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const asset = result.assets[0];

        // 3. Set Photo State with correct format for FastAPI FormData upload
        setPhotos(prev => ({
            ...prev,
            [key]: {
                uri: asset.uri,
                // Ensure unique name for storage: [key]_[original filename]
                name: `${key}_${asset.uri.split('/').pop()}`,
                type: 'image/jpeg', // Camera output type
            }
        }));
        Alert.alert('Photo Selected', asset.uri.split('/').pop());
      }
    } catch (e) {
      console.error("Image Picker Error:", e);
      Alert.alert('Error', 'Failed to capture photo.');
    }
  };
  // --- END PRODUCTION FUNCTIONS ---

  const validateAndSubmit = () => {
    // 1. Validate mandatory fields
    const isIdValid = formData.application_id && formData.application_id.length > 5;
    const isGpsValid = formData.registered_lat && formData.registered_lon;
    const isPhotosValid = Object.values(photos).every(photo => photo !== null);

    if (!isIdValid) {
        Alert.alert('Error', 'Please enter a valid Application ID.');
        return;
    }
    if (!isGpsValid) {
      Alert.alert('Error', 'Please capture or manually enter GPS coordinates.');
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

    // 3. Append photo files (using the stored objects)
    for (const [key, photo] of Object.entries(photos)) {
      data.append(key, photo);
    }

    try {
      // Calls the submission endpoint to upload files and start verification
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
        disabled={loading}
      >
        <Text style={styles.photoButtonText}>
          {photos[photoKey] ? `✅ Selected: ${photos[photoKey].name.substring(0, 20)}...` : 'Capture Photo'}
        </Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Verification Submission (Step 2)</Text>

      {/* --- 1. Application ID --- */}
      <TextInput
        style={styles.input}
        placeholder="Enter Application ID *"
        value={formData.application_id}
        onChangeText={(text) => handleFieldChange('application_id', text)}
        editable={!applicationId && !loading}
      />

      <Text style={styles.header}>Capture Site Location *</Text>

      {/* --- Location Input (Manual/Display) --- */}
      <View style={styles.locationSection}>
        <TextInput
            style={[styles.input, styles.halfInput]}
            placeholder="Latitude"
            value={formData.registered_lat}
            onChangeText={(text) => handleFieldChange('registered_lat', text)}
            keyboardType="numeric"
            editable={!loading}
        />
        <TextInput
            style={[styles.input, styles.halfInput]}
            placeholder="Longitude"
            value={formData.registered_lon}
            onChangeText={(text) => handleFieldChange('registered_lon', text)}
            keyboardType="numeric"
            editable={!loading}
        />
      </View>

      {/* --- Location Capture Button (Automatic) --- */}
      <TouchableOpacity style={styles.locationButton} onPress={handleGetLocation} disabled={loading}>
          <Text style={styles.buttonText}>
            {loading && formData.registered_lat === '' ? 'Capturing GPS...' : 'Capture Current GPS Location'}
          </Text>
      </TouchableOpacity>

      {/* --- 2. Photo Uploads --- */}
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