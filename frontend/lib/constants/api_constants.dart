class ApiConstants {
  // Android emulator  → http://10.0.2.2:8001
  // Physical device   → http://<your-wifi-ip>:8001  (e.g. http://192.168.8.100:8001)
  // Flutter Web       → http://127.0.0.1:8001
  static const String baseUrl = "http://192.168.8.100:8001";

  // Outfit Compatibility API endpoint
  static const String generateOutfitsEndpoint = "$baseUrl/outfits/generate";

  // Saved Outfit API endpoints
  static String saveOutfitEndpoint(String outfitId) {
    return "$baseUrl/saved-outfits/save/$outfitId";
  }

  static String getSavedOutfitsEndpoint(String userId) {
    return "$baseUrl/saved-outfits/$userId";
  }

  static String savedOutfitDetailEndpoint(String outfitId) {
    return "$baseUrl/saved-outfits/detail/$outfitId";
  }

  static String removeSavedOutfitEndpoint(String outfitId) {
    return "$baseUrl/saved-outfits/$outfitId";
  }
}
