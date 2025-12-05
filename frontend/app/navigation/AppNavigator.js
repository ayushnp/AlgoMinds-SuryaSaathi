import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import AuthScreen from '../screens/AuthScreen';
import HomeScreen from '../screens/HomeScreen';
import ApplicationFormScreen from '../screens/ApplicationFormScreen';
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
        <Stack.Screen
          name="ApplicationForm"
          component={ApplicationFormScreen}
          options={{ title: 'New Application' }}
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
