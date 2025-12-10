import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator, 
  Platform, 
} from 'react-native';
// NEW IMPORTS FOR PRODUCTION
import * as Location from 'expo-location';
import * as ImagePicker from 'expo-image-picker';
import { MaterialIcons } from '@expo/vector-icons'; 

import { applicationAPI } from '../services/api';


// --- COLOR CONSTANTS ---
const PRIMARY_COLOR = '#007AFF';
const ACCENT_COLOR = '#FF9800';
const SUCCESS_COLOR = '#4CAF50';
const BACKGROUND_COLOR = '#F9F9F9';
const CARD_COLOR = 'white';
// ---------------------------------------------------------------------------------


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
  const [isLocationLoading, setIsLocationLoading] = useState(false); // Separate loading for better UX

  const handleFieldChange = (key, value) => {
    setFormData({ ...formData, [key]: value });
  };

  // --- PRODUCTION GPS LOCATION CAPTURE (kept for context) ---
  const handleGetLocation = async () => {
    setIsLocationLoading(true);
    try {
      let { status: foregroundStatus } = await Location.requestForegroundPermissionsAsync();
      if (foregroundStatus !== 'granted') {
        Alert.alert('Permission Denied', 'Please grant location access to capture site coordinates.');
        return;
      }
      let location = await Location.getCurrentPositionAsync({
          accuracy: Location.Accuracy.BestForNavigation,
          mayShareAddress: true 
      });
      const { latitude, longitude } = location.coords;
      setFormData(prev => ({
        ...prev,
        registered_lat: latitude.toString(),
        registered_lon: longitude.toString()
      }));
      Alert.alert('Location Captured', `Lat: ${latitude.toFixed(6)}, Lon: ${longitude.toFixed(6)}`);
    } catch (e) {
      console.error("Location Error:", e);
      Alert.alert('Error', 'Failed to get location. Ensure GPS is enabled and permissions are granted.');
    } finally {
        setIsLocationLoading(false);
    }
  };

  // --- UPDATED PRODUCTION CAMERA/IMAGE PICKER CAPTURE ---
  const handlePickPhoto = async (key) => {
    const options = {
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: false,
      quality: 0.7,
    };

    const processResult = (result) => {
        if (!result.canceled && result.assets && result.assets.length > 0) {
            const asset = result.assets[0];
            setPhotos(prev => ({
                ...prev,
                [key]: {
                    uri: asset.uri,
                    name: `${key}_${asset.uri.split('/').pop()}`,
                    type: 'image/jpeg',
                }
            }));
            Alert.alert('Photo Selected', `Captured: ${key}`);
        }
    };
    
    // Function to launch the Camera
    const launchCamera = async () => {
        try {
            const { status } = await ImagePicker.requestCameraPermissionsAsync();
            if (status !== 'granted') {
                Alert.alert('Permission Denied', 'Camera permission is required.');
                return;
            }
            const result = await ImagePicker.launchCameraAsync(options);
            processResult(result);
        } catch (e) {
            console.error("Camera Error:", e);
            Alert.alert('Error', 'Failed to launch camera.');
        }
    };

    // Function to launch the Image Library
    const launchLibrary = async () => {
        try {
            const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
            if (status !== 'granted') {
                Alert.alert('Permission Denied', 'Media Library permission is required.');
                return;
            }
            const result = await ImagePicker.launchImageLibraryAsync(options);
            processResult(result);
        } catch (e) {
            console.error("Library Error:", e);
            Alert.alert('Error', 'Failed to open image library.');
        }
    };

    if (Platform.OS === 'web') {
        // Web only allows library selection
        launchLibrary();
    } else {
        // Native (iOS/Android) provides a choice
        Alert.alert(
            "Select Photo Source",
            "Choose whether to capture a new photo or select one from your library.",
            [
                { text: "Take Photo", onPress: launchCamera },
                { text: "Choose from Library", onPress: launchLibrary },
                { text: "Cancel", style: "cancel" }
            ],
            { cancelable: true }
        );
    }
  };
  // --- END PRODUCTION FUNCTIONS ---

  const validateAndSubmit = () => {
    // 1. Validate mandatory fields
    const isIdValid = formData.application_id && formData.application_id.length > 5;
    const isGpsValid = parseFloat(formData.registered_lat) && parseFloat(formData.registered_lon);
    const isPhotosValid = Object.values(photos).every(photo => photo !== null);

    if (!isIdValid) {
        Alert.alert('Validation Error', 'Please enter a valid Application ID (length > 5).');
        return;
    }
    if (!isGpsValid) {
      Alert.alert('Validation Error', 'Please capture or manually enter valid GPS coordinates (numbers).');
      return;
    }
    if (!isPhotosValid) {
      Alert.alert('Validation Error', 'Please upload all three required photos.');
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

  // Custom component for photo capture buttons with visual status
  const PhotoPicker = ({ label, photoKey }) => {
    const isSelected = photos[photoKey] !== null;
    const photoName = isSelected ? photos[photoKey].name.substring(0, 20) : 'Capture Photo';
    const buttonText = Platform.OS === 'web' 
        ? (isSelected ? 'Re-select' : 'Select File') 
        : (isSelected ? 'Change Photo' : 'Select Photo');


    return (
        <View style={styles.photoCard}>
            <Text style={styles.photoLabel}>{label} *</Text>
            
            <View style={styles.photoActionContainer}>
              <View style={styles.photoStatus}>
                  {isSelected ? (
                    <MaterialIcons name="check-circle" size={24} color={SUCCESS_COLOR} /> 
                  ) : (
                    <MaterialIcons name="camera-alt" size={24} color={ACCENT_COLOR} /> 
                  )}
                  <Text style={[styles.photoStatusText, isSelected && styles.photoStatusTextSelected]}>
                    {isSelected ? `Selected: ${photoName}...` : 'Awaiting Selection'}
                  </Text>
              </View>

              <TouchableOpacity
                style={[styles.captureButton, isSelected ? styles.captureButtonSelected : styles.captureButtonDefault]}
                onPress={() => handlePickPhoto(photoKey)}
                disabled={loading || isLocationLoading}
              >
                <Text style={styles.captureButtonText}>
                  {buttonText}
                </Text>
              </TouchableOpacity>
            </View>
        </View>
    );
  };

  // Custom component for section headers
  const RenderSectionHeader = ({ title }) => (
    <View style={styles.sectionHeader}>
        <Text style={styles.headerText}>{title}</Text>
        <View style={styles.divider} />
    </View>
  );

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <Text style={styles.title}>Solar Verification</Text>
      <Text style={styles.subtitle}>Step 2: Site Location & Photo Submission</Text>


      {/* --- SECTION: Application ID --- */}
      <RenderSectionHeader title="Application Details" />
      <TextInput
        style={styles.input}
        placeholder="Enter Application ID *"
        value={formData.application_id}
        onChangeText={(text) => handleFieldChange('application_id', text)}
        editable={!applicationId && !loading}
      />
      
      {/* --- SECTION: Capture Site Location --- */}
      <RenderSectionHeader title="Capture Site Location" />

      {/* --- Location Capture Button (Automatic) --- */}
      <TouchableOpacity 
        style={[styles.locationButton, (loading || isLocationLoading) && styles.buttonDisabled]} 
        onPress={handleGetLocation} 
        disabled={loading || isLocationLoading}
      >
          {isLocationLoading ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text style={styles.buttonText}>Get Current GPS Location</Text>
          )}
      </TouchableOpacity>

      {/* --- Location Input (Manual/Display) --- */}
      <View style={styles.locationSection}>
        <TextInput
            style={[styles.input, styles.halfInput]}
            placeholder="Latitude (e.g., 28.7041)"
            value={formData.registered_lat}
            onChangeText={(text) => handleFieldChange('registered_lat', text.replace(/[^0-9.-]/g, ''))} // Allow numbers, decimal, and sign
            keyboardType="numeric"
            editable={!loading && !isLocationLoading}
        />
        <TextInput
            style={[styles.input, styles.halfInput]}
            placeholder="Longitude (e.g., 77.1025)"
            value={formData.registered_lon}
            onChangeText={(text) => handleFieldChange('registered_lon', text.replace(/[^0-9.-]/g, ''))} // Allow numbers, decimal, and sign
            keyboardType="numeric"
            editable={!loading && !isLocationLoading}
        />
      </View>


      {/* --- SECTION: Photo Uploads --- */}
      <RenderSectionHeader title="Required Verification Photos" />
      <PhotoPicker label="1. Wide Rooftop Photo" photoKey="wide_rooftop_photo" />
      <PhotoPicker label="2. Serial Number Close-up" photoKey="serial_number_photo" />
      <PhotoPicker label="3. Inverter Installation Photo" photoKey="inverter_photo" />

      <View style={styles.spacer} />

      {/* --- SUBMIT BUTTON --- */}
      <TouchableOpacity
        style={[styles.submitButton, loading && styles.buttonDisabled]}
        onPress={validateAndSubmit}
        disabled={loading}
      >
        {loading ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text style={styles.buttonText}>Submit Verification</Text>
          )}
      </TouchableOpacity>
    </ScrollView>
  );
}

// --- STYLES ---

const styles = StyleSheet.create({
  
  container: { 
    flex: 1, 
    backgroundColor: BACKGROUND_COLOR,
  },
  contentContainer: {
    padding: 20, 
    paddingBottom: 40,
  },
  title: { 
    fontSize: 28, 
    fontWeight: '700', 
    marginBottom: 5, 
    color: PRIMARY_COLOR, 
    textAlign: 'center' 
  },
  subtitle: { 
    fontSize: 16, 
    color: '#666', 
    marginBottom: 25, 
    textAlign: 'center' 
  },
  
  // Section Header Styling
  sectionHeader: { 
    marginTop: 15, 
    marginBottom: 15,
  },
  headerText: { 
    fontSize: 18, 
    fontWeight: 'bold', 
    color: '#333', 
    marginBottom: 8,
  },
  divider: {
    height: 2,
    backgroundColor: ACCENT_COLOR,
    width: 60,
  },

  // Input & Location Styling
  input: { 
    backgroundColor: CARD_COLOR, 
    borderWidth: 1, 
    borderColor: '#ddd', 
    padding: Platform.OS === 'ios' ? 15 : 10,
    marginBottom: 10, 
    borderRadius: 8, 
    fontSize: 16,
    color: '#333'
  },
  locationSection: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    marginBottom: 20 
  },
  halfInput: { 
    width: '48%', 
    marginBottom: 0,
  },

  // Location Button Styling
  locationButton: { 
    backgroundColor: PRIMARY_COLOR, 
    padding: 15, 
    borderRadius: 10, 
    alignItems: 'center', 
    marginBottom: 10,
    ...Platform.select({
      ios: { shadowColor: '#000', shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.2, shadowRadius: 3 },
      android: { elevation: 5 },
    }),
  },
  
  // Photo Picker Card Styling
  photoCard: {
    backgroundColor: CARD_COLOR,
    padding: 15,
    borderRadius: 10,
    marginBottom: 15,
    borderLeftWidth: 5,
    borderLeftColor: ACCENT_COLOR,
    ...Platform.select({
        ios: { shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1, shadowRadius: 2 },
        android: { elevation: 3 },
    }),
  },
  photoLabel: { 
    fontSize: 15, 
    fontWeight: '600', 
    color: '#333', 
    marginBottom: 10 
  },
  photoActionContainer: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center' 
  },
  photoStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  photoStatusText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  photoStatusTextSelected: {
    color: SUCCESS_COLOR,
    fontWeight: 'bold',
  },
  captureButton: { 
    paddingVertical: 8, 
    paddingHorizontal: 15, 
    borderRadius: 20, 
    alignItems: 'center',
  },
  captureButtonDefault: { 
    backgroundColor: ACCENT_COLOR, 
  },
  captureButtonSelected: {
    backgroundColor: PRIMARY_COLOR,
  },
  captureButtonText: { 
    color: 'white', 
    fontSize: 14, 
    fontWeight: 'bold' 
  },

  // Submit Button Styling
  submitButton: { 
    backgroundColor: ACCENT_COLOR, 
    padding: 18, 
    borderRadius: 10, 
    alignItems: 'center', 
    marginTop: 30, 
    marginBottom: 30,
    ...Platform.select({
        ios: { shadowColor: '#000', shadowOffset: { width: 0, height: 5 }, shadowOpacity: 0.3, shadowRadius: 5 },
        android: { elevation: 8 },
    }),
  },
  buttonDisabled: { 
    opacity: 0.6 
  },
  buttonText: { 
    color: 'white', 
    fontSize: 18, 
    fontWeight: 'bold' 
  },
  spacer: {
    height: 20, // Add space before the submit button
  }
});