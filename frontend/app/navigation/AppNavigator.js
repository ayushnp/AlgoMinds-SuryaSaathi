// In frontend/app/navigation/AppNavigator.js

import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import AuthScreen from '../screens/AuthScreen';
import HomeScreen from '../screens/HomeScreen';
// Import the new/renamed screens
import InitialApplicationFormScreen from '../screens/InitialApplicationFormScreen';
import VerificationFormScreen from '../screens/VerificationFormScreen';
import ApplicationListScreen from '../screens/ApplicationListScreen';

const Stack = createStackNavigator();

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="Auth"
        screenOptions={{
          headerStyle: { backgroundColor: '#FF9800' },
          headerTintColor: '#fff',
          headerTitleStyle: { fontWeight: 'bold' },
        }}
      >
        <Stack.Screen
          name="Auth"
          component={AuthScreen}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="Home"
          component={HomeScreen}
          options={{ title: 'Suryamitra', headerLeft: null }}
        />
        {/* Step 1 Screen: Initial Application */}
        <Stack.Screen
          name="InitialApplicationForm" 
          component={InitialApplicationFormScreen}
          options={{ title: 'New Application (Step 1)' }}
        />
        {/* Step 2 Screen: Verification Submission */}
        <Stack.Screen
          name="VerificationForm"
          component={VerificationFormScreen}
          options={{ title: 'Verification (Step 2)' }}
        />
        <Stack.Screen
          name="ApplicationList"
          component={ApplicationListScreen}
          options={{ title: 'My Applications' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}