import AsyncStorage from '@react-native-async-storage/async-storage';

export const saveApplicationId = async (applicationId) => {
  try {
    const stored = await AsyncStorage.getItem('application_ids');
    const ids = stored ? JSON.parse(stored) : [];

    if (!ids.includes(applicationId)) {
      ids.push(applicationId);
      await AsyncStorage.setItem('application_ids', JSON.stringify(ids));
    }
  } catch (error) {
    console.error('Error saving application ID:', error);
  }
};
